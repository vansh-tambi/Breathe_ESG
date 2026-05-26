import csv
import io
import uuid
from decimal import Decimal
from datetime import datetime

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.ingestion.models import RawRecord, DataSource
from apps.normalization.models import NormalizedRecord

# Unit conversion map for distance units
UNIT_NORMALIZATION_MAP = {
    'KM': ('Kilometers', Decimal('1.0')),
    'KILOMETERS': ('Kilometers', Decimal('1.0')),
    'MILES': ('Kilometers', Decimal('1.60934')),
    'MI': ('Kilometers', Decimal('1.60934')),
}

# Allowed travel categories
TRAVEL_CATEGORIES = {
    'flight': 'flight',
    'hotel': 'hotel',
    'ground': 'ground',
}

def parse_date(date_str):
    """Parse common date formats into a ``datetime.date``.
    Supports ISO (YYYY-MM-DD), European (DD/MM/YYYY) and US (MM/DD/YYYY).
    """
    date_str = date_str.strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date '{date_str}'. Expected ISO or common European/US formats.")

def clean_decimal(value_str):
    """Convert a string to ``Decimal`` safely. Empty strings become 0.
    Handles commas as decimal separators.
    """
    value_str = value_str.strip()
    if not value_str:
        return Decimal('0')
    # Replace comma decimal separator with dot
    if ',' in value_str and '.' not in value_str:
        value_str = value_str.replace(',', '.')
    try:
        return Decimal(value_str)
    except Exception:
        raise ValueError(f"Unable to parse '{value_str}' as a decimal number.")

def process_travel_csv(company, data_source, file_handle):
    """Process a Concur‑style travel CSV file.

    The function creates ``RawRecord`` entries for auditability and a corresponding
    ``NormalizedRecord`` that captures travel‑specific attributes.
    """
    REQUIRED_HEADERS = [
        'Category',          # flight / hotel / ground (case‑insensitive)
        'Date',              # date of travel activity
        'Origin',            # IATA code (or hotel city) – optional for hotel
        'Destination',       # IATA code (or hotel city) – optional for hotel
        'Distance',          # numeric distance, may be empty for hotel stays
        'Unit',              # KM, MILES etc.
    ]

    file_data = file_handle.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))

    # Validate headers
    headers = [h.strip() for h in (csv_reader.fieldnames or [])]
    missing = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing:
        raise ValidationError(f"Missing required travel CSV headers: {', '.join(missing)}")

    job_id = uuid.uuid4()
    saved = 0
    failed = 0
    errors = []

    with transaction.atomic():
        for line_idx, row in enumerate(csv_reader, start=1):
            # Normalise keys
            row = {k.strip(): (v.strip() if v else '') for k, v in row.items() if k}

            raw_record = RawRecord.objects.create(
                company=company,
                data_source=data_source,
                job_id=job_id,
                sequence_number=line_idx,
                raw_payload=row,
                processing_state='UNPROCESSED'
            )

            try:
                # Category handling
                cat_raw = row.get('Category', '').lower()
                if cat_raw not in TRAVEL_CATEGORIES:
                    raise ValueError(f"Unsupported travel category '{cat_raw}'.")
                travel_category = TRAVEL_CATEGORIES[cat_raw]

                # Date parsing
                travel_date = parse_date(row.get('Date', ''))

                # Airport code handling – store as‑is (allow empty strings)
                origin_code = row.get('Origin', '') or None
                destination_code = row.get('Destination', '') or None

                # Distance handling – may be missing for hotel stays
                distance_str = row.get('Distance', '')
                unit_raw = row.get('Unit', '').upper()

                if distance_str:
                    raw_distance = clean_decimal(distance_str)
                    if unit_raw not in UNIT_NORMALIZATION_MAP:
                        raise ValueError(f"Unrecognised distance unit '{unit_raw}'.")
                    norm_unit_name, multiplier = UNIT_NORMALIZATION_MAP[unit_raw]
                    distance_km = (raw_distance * multiplier).quantize(Decimal('0.01'))
                else:
                    # Missing distance – flag as None; later logic may decide to reject
                    distance_km = None

                # Emission factor – simple placeholder for demonstration
                # Flight: 0.115 kg CO₂e per passenger‑km, Hotel & Ground: 0.05 kg CO₂e per km
                if travel_category == 'flight':
                    ef = Decimal('0.115')
                else:
                    ef = Decimal('0.05')

                co2e = (distance_km * ef / Decimal('1000')) if distance_km is not None else Decimal('0')

                # Normalized record creation
                NormalizedRecord.objects.create(
                    company=company,
                    raw_record=raw_record,
                    activity_type='BUSINESS_TRAVEL',
                    scope_classification='SCOPE_3',
                    reporting_date=travel_date,
                    raw_quantity=distance_km if distance_km is not None else Decimal('0'),
                    raw_unit='Kilometers',
                    normalized_quantity=distance_km if distance_km is not None else Decimal('0'),
                    normalized_unit='Kilometers',
                    travel_category=travel_category,
                    origin_airport_code=origin_code,
                    destination_airport_code=destination_code,
                    distance_km=distance_km,
                    emission_factor_applied=ef,
                    co2e_metric_tons=co2e,
                    review_status='PENDING_REVIEW',
                    is_locked=False,
                )

                raw_record.processing_state = 'NORMALIZED'
                raw_record.save()
                saved += 1
            except Exception as exc:
                raw_record.processing_state = 'REJECTED'
                raw_record.structural_error = str(exc)
                raw_record.save()
                failed += 1
                errors.append({"line_number": line_idx, "reason": str(exc)})

    return {
        "job_id": str(job_id),
        "status": "COMPLETED" if failed == 0 else "PARTIALLY_FAILED",
        "processed_records_count": saved,
        "failed_records_count": failed,
        "errors": errors,
    }
