import csv
import io
import uuid
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.ingestion.models import RawRecord
from apps.normalization.models import NormalizedRecord
from apps.common.utils import parse_date_flexible, clean_decimal_flexible, validate_csv_headers

UNIT_NORMALIZATION_MAP = {
    'KM': ('Kilometers', Decimal('1.0')),
    'KILOMETERS': ('Kilometers', Decimal('1.0')),
    'MILES': ('Kilometers', Decimal('1.60934')),
    'MI': ('Kilometers', Decimal('1.60934')),
}

TRAVEL_CATEGORIES = {
    'flight': 'flight',
    'hotel': 'hotel',
    'ground': 'ground',
}

def process_travel_csv(company, data_source, file_handle):
    """
    Parse travel CSV, validate headers, convert distances, and save raw and normalized records.
    """
    REQUIRED_HEADERS = [
        'Category',
        'Date',
        'Origin',
        'Destination',
        'Distance',
        'Unit',
    ]

    file_data = file_handle.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))

    validate_csv_headers(csv_reader.fieldnames, REQUIRED_HEADERS, "Missing required travel CSV headers")

    job_id = uuid.uuid4()
    saved = 0
    failed = 0
    errors = []

    with transaction.atomic():
        for line_idx, row in enumerate(csv_reader, start=1):
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
                cat_raw = row.get('Category', '').lower()
                if cat_raw not in TRAVEL_CATEGORIES:
                    raise ValueError(f"Unsupported travel category '{cat_raw}'.")
                travel_category = TRAVEL_CATEGORIES[cat_raw]

                travel_date = parse_date_flexible(row.get('Date', ''))

                origin_code = row.get('Origin', '') or None
                destination_code = row.get('Destination', '') or None

                distance_str = row.get('Distance', '')
                unit_raw = row.get('Unit', '').upper()

                if distance_str:
                    raw_distance = clean_decimal_flexible(distance_str)
                    if unit_raw not in UNIT_NORMALIZATION_MAP:
                        raise ValueError(f"Unrecognised distance unit '{unit_raw}'.")
                    norm_unit_name, multiplier = UNIT_NORMALIZATION_MAP[unit_raw]
                    distance_km = (raw_distance * multiplier).quantize(Decimal('0.01'))
                else:
                    distance_km = None

                if travel_category == 'flight':
                    ef = Decimal('0.115')
                else:
                    ef = Decimal('0.05')

                co2e = (distance_km * ef / Decimal('1000')) if distance_km is not None else Decimal('0')

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
