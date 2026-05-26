import csv
import io
import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.ingestion.models import RawRecord
from apps.normalization.models import NormalizedRecord
from apps.common.utils import parse_date_flexible, clean_decimal_flexible, validate_csv_headers

def parse_billing_period(range_str):
    """
    Split and parse a billing period interval string (e.g. '2025-11-01 - 2025-11-30') into start and end dates.
    """
    range_str = range_str.strip()
    separators = (' - ', ' to ', '-', 'to')
    for sep in separators:
        if sep in range_str:
            parts = range_str.split(sep)
            if len(parts) == 2:
                try:
                    start_date = parse_date_flexible(parts[0])
                    end_date = parse_date_flexible(parts[1])
                    return start_date, end_date
                except ValueError:
                    continue
    raise ValueError(f"Unable to split billing interval '{range_str}' using standard separators.")


def split_billing_period_pro_rata(start_date, end_date, total_consumption):
    """
    Linearly split consumption across calendar month segments within a billing period.
    """
    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        raise ValueError("Billing period start date must precede or equal the end date.")
        
    daily_rate = Decimal(total_consumption) / Decimal(total_days)
    splits = []
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.month == 12:
            next_month_start = date(current_date.year + 1, 1, 1)
        else:
            next_month_start = date(current_date.year, current_date.month + 1, 1)
            
        month_end = next_month_start - timedelta(days=1)
        segment_end = min(month_end, end_date)
        segment_days = (segment_end - current_date).days + 1
        segment_consumption = daily_rate * Decimal(segment_days)
        
        splits.append({
            "reporting_date": segment_end,
            "segment_days": segment_days,
            "consumption": segment_consumption
        })
        
        current_date = segment_end + timedelta(days=1)
        
    return splits


def process_utility_csv(company, data_source, file_handle):
    """
    Parse utility portal CSV, perform pro-rata calendar calculations, flag outliers, and save records.
    """
    REQUIRED_HEADERS = ['meter_id', 'billing_period', 'consumption', 'unit']
    
    file_data = file_handle.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))
    
    validate_csv_headers(csv_reader.fieldnames, REQUIRED_HEADERS, "Missing required portal headers")
        
    job_id = uuid.uuid4()
    records_saved = 0
    records_failed = 0
    failures_log = []
    
    # Thresholds for Outlier Detection (kWh)
    DAILY_CONSUMPTION_SUSPICIOUS_LIMIT = Decimal('5000.0000')
    TOTAL_AGGREGATED_SUSPICIOUS_LIMIT = Decimal('150000.0000')
    
    with transaction.atomic():
        for line_idx, row in enumerate(csv_reader, start=1):
            row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            
            raw_record = RawRecord.objects.create(
                company=company,
                data_source=data_source,
                job_id=job_id,
                sequence_number=line_idx,
                raw_payload=row,
                processing_state='UNPROCESSED'
            )
            
            try:
                raw_qty_str = row.get('consumption', '')
                raw_quantity = clean_decimal_flexible(raw_qty_str)
                
                raw_unit = row.get('unit', '').upper()
                if raw_unit == 'MWH':
                    normalized_quantity = raw_quantity * Decimal('1000.0000')
                    norm_unit = 'kWh'
                elif raw_unit == 'KWH':
                    normalized_quantity = raw_quantity
                    norm_unit = 'kWh'
                else:
                    raise ValueError(f"Unsupported utility energy unit '{raw_unit}'. MWh or kWh only.")
                
                billing_str = row.get('billing_period', '')
                start_date, end_date = parse_billing_period(billing_str)
                
                segments = split_billing_period_pro_rata(start_date, end_date, normalized_quantity)
                
                total_days = (end_date - start_date).days + 1
                daily_usage = normalized_quantity / Decimal(total_days)
                
                for seg in segments:
                    seg_qty = seg["consumption"]
                    seg_date = seg["reporting_date"]
                    
                    # Electricity Scope 2 emissions factor (0.385 kg CO2e / kWh)
                    factor = Decimal('0.38500000')
                    co2e_val = (seg_qty * factor) / Decimal('1000.0')
                    
                    is_suspicious = False
                    warning_note = ""
                    
                    if daily_usage > DAILY_CONSUMPTION_SUSPICIOUS_LIMIT:
                        is_suspicious = True
                        warning_note = f"[SUSPICIOUS] High usage rate: {daily_usage:.2f} kWh/day exceeds threshold."
                    elif seg_qty > TOTAL_AGGREGATED_SUSPICIOUS_LIMIT:
                        is_suspicious = True
                        warning_note = f"[SUSPICIOUS] Large aggregated volume: {seg_qty:.2f} kWh exceeds threshold."
                        
                    NormalizedRecord.objects.create(
                        company=company,
                        raw_record=raw_record,
                        activity_type='ELECTRICITY_CONSUMPTION',
                        scope_classification='SCOPE_2',
                        reporting_date=seg_date,
                        raw_quantity=raw_quantity,
                        raw_unit=row.get('unit', ''),
                        normalized_quantity=seg_qty,
                        normalized_unit=norm_unit,
                        emission_factor_applied=factor,
                        co2e_metric_tons=co2e_val,
                        review_status='SUSPICIOUS' if is_suspicious else 'PENDING_REVIEW',
                        analyst_notes=warning_note,
                        is_locked=False
                    )
                
                raw_record.processing_state = 'NORMALIZED'
                raw_record.save()
                records_saved += 1
                
            except Exception as e:
                raw_record.processing_state = 'REJECTED'
                raw_record.structural_error = str(e)
                raw_record.save()
                
                records_failed += 1
                failures_log.append({
                    "line_number": line_idx,
                    "reason": str(e)
                })
                
    return {
        "job_id": str(job_id),
        "status": "COMPLETED" if records_failed == 0 else "PARTIALLY_FAILED",
        "processed_records_count": records_saved,
        "failed_records_count": records_failed,
        "errors": failures_log
    }
