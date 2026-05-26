from datetime import datetime
from decimal import Decimal
from django.core.exceptions import ValidationError

def parse_date_flexible(date_str):
    """
    Parse date string into a date object trying common formats dynamically.
    """
    date_str = date_str.strip()
    formats = ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d')
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date '{date_str}'. Unsupported format.")


def clean_decimal_flexible(value_str):
    """
    Safely convert numeric string (including German or comma decimal notations) to Decimal.
    """
    value_str = value_str.strip()
    if not value_str:
        return Decimal('0.0000')
    
    # Handle German or comma-based decimals
    if '.' in value_str and ',' in value_str:
        value_str = value_str.replace('.', '').replace(',', '.')
    elif ',' in value_str:
        value_str = value_str.replace(',', '.')
        
    try:
        return Decimal(value_str)
    except Exception:
        raise ValueError(f"Unable to parse '{value_str}' as a valid decimal number.")


def validate_csv_headers(fieldnames, required_headers, error_message_prefix="Missing required headers"):
    """
    Validate that all required headers are present in the CSV fieldnames.
    """
    headers = [h.strip() for h in (fieldnames or [])]
    missing = [h for h in required_headers if h not in headers]
    if missing:
        raise ValidationError(f"{error_message_prefix}: {', '.join(missing)}")
