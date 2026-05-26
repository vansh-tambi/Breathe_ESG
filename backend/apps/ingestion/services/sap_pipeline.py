import csv
import io
import uuid
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.ingestion.models import RawRecord, PlantLookup
from apps.normalization.models import NormalizedRecord

# ------------------------------------------------------------------------------
# Unit Normalization & Mapping Registry
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Localized Parsers Helpers
# ------------------------------------------------------------------------------
def clean_german_decimal(value_str):
    """
    Cleanses localized German number formatting strings to standard Decimal targets.
    Example: '1.500,50' -> Decimal('1500.50')
    """
    value_str = value_str.strip()
    if not value_str:
        return Decimal('0.0000')
    
    # German notation contains both thousands dots and decimal commas
    if '.' in value_str and ',' in value_str:
        value_str = value_str.replace('.', '').replace(',', '.')
    # Contains decimal commas only
    elif ',' in value_str:
        value_str = value_str.replace(',', '.')
        
    try:
        return Decimal(value_str)
    except Exception:
        raise ValueError(f"Unable to parse '{value_str}' as a valid decimal number.")


def parse_german_date(date_str):
    """
    Parses German standard dot formatted date strings to datetime.date objects.
    Example: '24.12.2025' -> datetime.date(2025, 12, 24)
    """
    date_str = date_str.strip()
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%Y%m%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date '{date_str}'. Expected German dot format (DD.MM.YYYY).")


# ------------------------------------------------------------------------------
# Calculation & Factor Matching Core
# ------------------------------------------------------------------------------
def resolve_emissions_profile(material_text, normalized_qty, normalized_unit):
    """
    Resolves carbon emissions factors and maps raw units to target accounting variables.
    """
    text_upper = material_text.upper()
    
    # 1. Stationary Combustion: Diesel or Heating Oil
    if any(tag in text_upper for tag in ('DIESEL', 'HEIZOEL', 'HEATING OIL', 'FUEL OIL')):
        activity_type = 'FUEL_COMBUSTION'
        scope_classification = 'SCOPE_1'
        target_unit = 'Liters'
        
        # Standardize raw measurements to target Liters using typical fuel densities
        if normalized_unit == 'Metric Tons':
            # 1 Ton = ~1190 Liters of Heating Oil
            quantity = normalized_qty * Decimal('1190.0000')
        elif normalized_unit == 'Kilograms':
            # 1 Kg = ~1.19 Liters
            quantity = normalized_qty * Decimal('1.1900')
        elif normalized_unit == 'Liters':
            quantity = normalized_qty
        else:
            raise ValueError(f"Unsupported unit '{normalized_unit}' for fuel oil mapping.")
            
        # Standard EPA/DEFRA factor: 2.684 kg CO2e per Liter of Fuel Oil
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
            
        # Standard factor: 2.021 kg CO2e per Cubic Meter of Natural Gas
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


# ------------------------------------------------------------------------------
# Core Ingestion Service Function
# ------------------------------------------------------------------------------
def process_sap_csv(company, data_source, file_handle):
    """
    Main ingestion engine loop. Processes CSV lines inside a single SQL transaction.
    """
    # Define required German column headers
    REQUIRED_HEADERS = [
        'Materialbeleg',   # Document ID
        'Buchungsdatum',   # Posting Date
        'Werk',            # Plant Code
        'Menge',           # Quantity
        'Einheit',         # Unit
        'Materialtext'     # Description
    ]
    
    file_data = file_handle.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))
    
    # 1. Structural Schema Validation
    headers = [h.strip() for h in (csv_reader.fieldnames or [])]
    missing_headers = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing_headers:
        raise ValidationError(f"Missing required German headers: {', '.join(missing_headers)}")
        
    job_id = uuid.uuid4()
    records_saved = 0
    records_failed = 0
    failures_log = []
    
    # 2. Transactional processing loop
    with transaction.atomic():
        for line_idx, row in enumerate(csv_reader, start=1):
            # Clean keys to prevent trailing space issues
            row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            
            # Persist raw record immediately to preserve historical trace
            raw_record = RawRecord.objects.create(
                company=company,
                data_source=data_source,
                job_id=job_id,
                sequence_number=line_idx,
                raw_payload=row,
                processing_state='UNPROCESSED'
            )
            
            try:
                # A. Extract & Cleanse numeric quantity
                raw_qty_str = row.get('Menge', '')
                raw_quantity = clean_german_decimal(raw_qty_str)
                
                # B. Extract & Validate units
                raw_unit = row.get('Einheit', '').upper()
                if raw_unit not in UNIT_NORMALIZATION_MAP:
                    raise ValueError(f"Unrecognized unit abbreviation '{raw_unit}'.")
                
                norm_unit_name, norm_multiplier = UNIT_NORMALIZATION_MAP[raw_unit]
                normalized_quantity = raw_quantity * norm_multiplier
                
                # C. Extract & Parse posting date
                raw_date_str = row.get('Buchungsdatum', '')
                reporting_date = parse_german_date(raw_date_str)
                
                # D. Resolve physical plant lookup mapping
                werk_code = row.get('Werk', '')
                try:
                    plant_map = PlantLookup.objects.get(company=company, sap_plant_code=werk_code)
                except PlantLookup.DoesNotExist:
                    raise ValueError(f"SAP Plant code '{werk_code}' is not configured in lookups.")
                
                # E. Perform carbon footprint calculations
                material_desc = row.get('Materialtext', '')
                act_type, scope_class, final_qty, final_unit, ef_applied, co2e_val = resolve_emissions_profile(
                    material_text=material_desc,
                    normalized_qty=normalized_quantity,
                    normalized_unit=norm_unit_name
                )
                
                # F. Write Normalized Record
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
                
                # Update Raw record state to success
                raw_record.processing_state = 'NORMALIZED'
                raw_record.save()
                records_saved += 1
                
            except Exception as e:
                # Gracefully catch row validation issues and mark Raw Record as Rejected
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
