import csv
import io
import uuid
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.ingestion.models import RawRecord, PlantLookup
from apps.normalization.models import NormalizedRecord
from apps.common.utils import parse_date_flexible, clean_decimal_flexible, validate_csv_headers

UNIT_NORMALIZATION_MAP = {
    'L': ('Liters', Decimal('1.0')),
    'LTR': ('Liters', Decimal('1.0')),
    'LIT': ('Liters', Decimal('1.0')),
    'LITER': ('Liters', Decimal('1.0')),
    'T': ('Metric Tons', Decimal('1.0')),
    'TO': ('Metric Tons', Decimal('1.0')),
    'TON': ('Metric Tons', Decimal('1.0')),
    'KG': ('Kilograms', Decimal('1.0')),
    'CBM': ('Cubic Meters', Decimal('1.0')),
    'M3': ('Cubic Meters', Decimal('1.0')),
}

def resolve_emissions_profile(material_text, normalized_qty, normalized_unit):
    """
    Map material description and normalized quantity to Scope classifications and emission factors.
    """
    text_upper = material_text.upper()
    
    # 1. Stationary Combustion: Diesel or Heating Oil
    if any(tag in text_upper for tag in ('DIESEL', 'HEIZOEL', 'HEATING OIL', 'FUEL OIL')):
        activity_type = 'FUEL_COMBUSTION'
        scope_classification = 'SCOPE_1'
        target_unit = 'Liters'
        
        if normalized_unit == 'Metric Tons':
            quantity = normalized_qty * Decimal('1190.0000')
        elif normalized_unit == 'Kilograms':
            quantity = normalized_qty * Decimal('1.1900')
        elif normalized_unit == 'Liters':
            quantity = normalized_qty
        else:
            raise ValueError(f"Unsupported unit '{normalized_unit}' for fuel oil mapping.")
            
        factor = Decimal('2.68400000')
        co2e = (quantity * factor) / Decimal('1000.0')
        return activity_type, scope_classification, quantity, target_unit, factor, co2e

    # 2. Stationary Combustion: Natural Gas
    elif any(tag in text_upper for tag in ('ERDGAS', 'NATURAL GAS', 'GAS')):
        activity_type = 'FUEL_COMBUSTION'
        scope_classification = 'SCOPE_1'
        target_unit = 'Cubic Meters'
        
        if normalized_unit == 'Cubic Meters':
            quantity = normalized_qty
        else:
            raise ValueError(f"Unsupported unit '{normalized_unit}' for gaseous fuels.")
            
        factor = Decimal('2.02100000')
        co2e = (quantity * factor) / Decimal('1000.0')
        return activity_type, scope_classification, quantity, target_unit, factor, co2e
        
    # 3. Fallback generic fuel combustion profile
    else:
        activity_type = 'FUEL_COMBUSTION'
        scope_classification = 'SCOPE_1'
        target_unit = normalized_unit
        factor = Decimal('2.50000000')
        co2e = (normalized_qty * factor) / Decimal('1000.0')
        return activity_type, scope_classification, normalized_qty, target_unit, factor, co2e


def process_sap_csv(company, data_source, file_handle):
    """
    Parse SAP CSV file, validate schema, normalize quantities, and write records in a single transaction.
    """
    REQUIRED_HEADERS = [
        'Materialbeleg',
        'Buchungsdatum',
        'Werk',
        'Menge',
        'Einheit',
        'Materialtext'
    ]
    
    file_data = file_handle.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))
    
    validate_csv_headers(csv_reader.fieldnames, REQUIRED_HEADERS, "Missing required German headers")
        
    job_id = uuid.uuid4()
    records_saved = 0
    records_failed = 0
    failures_log = []
    
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
                raw_qty_str = row.get('Menge', '')
                raw_quantity = clean_decimal_flexible(raw_qty_str)
                
                raw_unit = row.get('Einheit', '').upper()
                if raw_unit not in UNIT_NORMALIZATION_MAP:
                    raise ValueError(f"Unrecognized unit abbreviation '{raw_unit}'.")
                
                norm_unit_name, norm_multiplier = UNIT_NORMALIZATION_MAP[raw_unit]
                normalized_quantity = raw_quantity * norm_multiplier
                
                raw_date_str = row.get('Buchungsdatum', '')
                reporting_date = parse_date_flexible(raw_date_str)
                
                werk_code = row.get('Werk', '')
                if not werk_code:
                    raise ValueError("SAP Plant code (Werk) is missing or empty.")
                plant_map, _ = PlantLookup.objects.get_or_create(
                    company=company,
                    sap_plant_code=werk_code,
                    defaults={
                        'facility_name': f"Demo Facility {werk_code}",
                        'grid_region_code': "GLOBAL-GRID"
                    }
                )
                
                material_desc = row.get('Materialtext', '')
                act_type, scope_class, final_qty, final_unit, ef_applied, co2e_val = resolve_emissions_profile(
                    material_text=material_desc,
                    normalized_qty=normalized_quantity,
                    normalized_unit=norm_unit_name
                )
                
                NormalizedRecord.objects.create(
                    company=company,
                    raw_record=raw_record,
                    activity_type=act_type,
                    scope_classification=scope_class,
                    reporting_date=reporting_date,
                    raw_quantity=raw_quantity,
                    raw_unit=row.get('Einheit', ''),
                    normalized_quantity=final_qty,
                    normalized_unit=final_unit,
                    emission_factor_applied=ef_applied,
                    co2e_metric_tons=co2e_val,
                    review_status='PENDING_REVIEW',
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
