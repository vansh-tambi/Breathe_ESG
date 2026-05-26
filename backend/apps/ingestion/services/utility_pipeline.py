import csv
import io
import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.ingestion.models import RawRecord
from apps.normalization.models import NormalizedRecord

# ------------------------------------------------------------------------------
# Localized Date Range & Parsing Helpers
# ------------------------------------------------------------------------------
def parse_flexible_date(date_str):
    """
    Parses dynamic date formats commonly exported by energy portals.
    """
    date_str = date_str.strip()
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%Y%m%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date string '{date_str}'.")


def parse_billing_period(range_str):
    """
    Splits and parses a billing period interval string into start and end dates.
    Example: '2025-11-01 - 2025-11-30' -> (date(2025, 11, 1), date(2025, 11, 30))
    """
    range_str = range_str.strip()
    separators = (' - ', ' to ', '-', 'to')
    for sep in separators:
        if sep in range_str:
            parts = range_str.split(sep)
            if len(parts) == 2:
                try:
                    start_date = parse_flexible_date(parts[0])
                    end_date = parse_flexible_date(parts[1])
                    return start_date, end_date
                except ValueError:
                    continue
    raise ValueError(f"Unable to split billing interval '{range_str}' using standard separators.")


# ------------------------------------------------------------------------------
# Pro-Rata Calendar Splitting Engine
# ------------------------------------------------------------------------------
def split_billing_period_pro_rata(start_date, end_date, total_consumption):
    """
    Divides standard billing periods spanning calendar months into linear daily splits.
    """
    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        raise ValueError("Billing period start date must precede or equal the end date.")
        
    daily_rate = Decimal(total_consumption) / Decimal(total_days)
    splits = []
    current_date = start_date
    
    while current_date <= end_date:
        # Resolve the boundary of the current calendar month
        if current_date.month == 12:
            next_month_start = date(current_date.year + 1, 1, 1)
        else:
            next_month_start = date(current_date.year, current_date.month + 1, 1)
            
        month_end = next_month_start - timedelta(days=1)
        
        # Constrain the month boundary by the billing cycle end date
        segment_end = min(month_end, end_date)
        segment_days = (segment_end - current_date).days + 1
        
        segment_consumption = daily_rate * Decimal(segment_days)
        
        splits.append({
            "reporting_date": segment_end,  # Align target reporting to segment boundary
            "segment_days": segment_days,
            "consumption": segment_consumption
        })
        
        current_date = segment_end + timedelta(days=1)
        
    return splits


# ------------------------------------------------------------------------------
# Core Utility Ingestion Engine
# ------------------------------------------------------------------------------
def process_utility_csv(company, data_source, file_handle):
    """
    Main utility portal ingestion pipeline. Handles pro-rata splits and outliers.
    """
    REQUIRED_HEADERS = ['meter_id', 'billing_period', 'consumption', 'unit']
    
    file_data = file_handle.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))
    
    headers = [h.strip() for h in (csv_reader.fieldnames or [])]
    missing_headers = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing_headers:
        raise ValidationError(f"Missing required portal headers: {', '.join(missing_headers)}")
        
    job_id = uuid.uuid4()
    records_saved = 0
    records_failed = 0
    failures_log = []
    
    # Static Thresholds for Suspicious Detection
    DAILY_CONSUMPTION_SUSPICIOUS_LIMIT = Decimal('5000.0000')  # 5,000 kWh per day
    TOTAL_AGGREGATED_SUSPICIOUS_LIMIT = Decimal('150000.0000')  # 150,000 kWh in a single month
    
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
                # A. Parse raw consumption values
                raw_qty_str = row.get('consumption', '')
                raw_quantity = Decimal(raw_qty_str)
                
                # B. Standardize units and convert MWh -> kWh
                raw_unit = row.get('unit', '').upper()
                if raw_unit == 'MWH':
                    normalized_quantity = raw_quantity * Decimal('1000.0000')
                    norm_unit = 'kWh'
                elif raw_unit == 'KWH':
                    normalized_quantity = raw_quantity
                    norm_unit = 'kWh'
                else:
                    raise ValueError(f"Unsupported utility energy unit '{raw_unit}'. MWh or kWh only.")
                
                # C. Extract billing dates range
                billing_str = row.get('billing_period', '')
                start_date, end_date = parse_billing_period(billing_str)
                
                # D. Split spanning intervals pro-rata into calendar segments
                segments = split_billing_period_pro_rata(start_date, end_date, normalized_quantity)
                
                # E. Process and calculate emissions per calendar segment
                total_days = (end_date - start_date).days + 1
                daily_usage = normalized_quantity / Decimal(total_days)
                
                for seg in segments:
                    seg_qty = seg["consumption"]
                    seg_date = seg["reporting_date"]
                    
                    # Standard grid electricity Scope 2 factor: e.g. 0.385 kg CO2e per kWh
                    factor = Decimal('0.38500000')
                    co2e_val = (seg_qty * factor) / Decimal('1000.0')
                    
                    # Outlier Detection Rules
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
