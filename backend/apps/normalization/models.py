import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.ingestion.models import RawRecord

User = get_user_model()

class NormalizedRecord(models.Model):
    """
    Stores unified, carbon-mapped, and pro-rata allocated activity records ready for audit analysis.
    """
    ACTIVITY_TYPES = [
        ('FUEL_COMBUSTION', 'Stationary Fuel Combustion (Scope 1)'),
        ('ELECTRICITY_CONSUMPTION', 'Electricity Consumption (Scope 2)'),
        ('BUSINESS_TRAVEL', 'Corporate Business Travel (Scope 3)'),
    ]

    SCOPE_CLASSIFICATIONS = [
        ('SCOPE_1', 'Scope 1 - Direct Emissions'),
        ('SCOPE_2', 'Scope 2 - Indirect Grid Emissions'),
        ('SCOPE_3', 'Scope 3 - Value Chain Indirect'),
    ]

    REVIEW_STATUS_CHOICES = [
        ('PENDING_REVIEW', 'Awaiting Analyst Action'),
        ('SUSPICIOUS', 'Flagged as Statistical Outlier'),
        ('DISPUTED', 'Opened Back to Source Verification'),
        ('APPROVED', 'Certified by Analyst'),
        ('LOCKED', 'Locked for Compliance Audit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='normalized_records', db_index=True)
    raw_record = models.OneToOneField(RawRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='normalized')
    
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, db_index=True)
    scope_classification = models.CharField(max_length=30, choices=SCOPE_CLASSIFICATIONS, db_index=True)
    
    # Target date representing the physical date of resource consumption (or start of pro-rata slice)
    reporting_date = models.DateField(db_index=True)
    
    # Original Values
    raw_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    raw_unit = models.CharField(max_length=50)
    
    # Converted Values (Normalized to standard metric values, e.g. kWh, Liters, Passenger-KM)
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    normalized_unit = models.CharField(max_length=50)
    # Travel-specific fields (optional)
    travel_category = models.CharField(
        max_length=20,
        choices=[
            ('flight', 'Flight'),
            ('hotel', 'Hotel'),
            ('ground', 'Ground'),
        ],
        null=True,
        blank=True,
        help_text='Category of travel activity.'
    )
    origin_airport_code = models.CharField(max_length=10, null=True, blank=True, help_text='IATA code of origin airport')
    destination_airport_code = models.CharField(max_length=10, null=True, blank=True, help_text='IATA code of destination airport')
    distance_km = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='Travel distance in kilometers')
    
    # Calculation Audit Details
    emission_factor_applied = models.DecimalField(max_digits=18, decimal_places=8)
    co2e_metric_tons = models.DecimalField(max_digits=18, decimal_places=6)
    
    # Administrative & Verification Status
    review_status = models.CharField(max_length=30, choices=REVIEW_STATUS_CHOICES, default='PENDING_REVIEW', db_index=True)
    is_locked = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'normalized_records'
        ordering = ['-reporting_date']

    def __str__(self):
        return f"{self.activity_type} on {self.reporting_date}: {self.co2e_metric_tons} tCO2e"


class ReviewDecision(models.Model):
    """
    Captures human certification, disputes, or overrides of carbon metrics.
    This model is strictly write-once (immutable).
    """
    ACTION_CHOICES = [
        ('APPROVE', 'Certified and Approved'),
        ('DISPUTE', 'Disputed Back to Source'),
        ('FLAG_SUSPICIOUS', 'Flagged as Outlier / Suspicious'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='review_decisions', db_index=True)
    normalized_record = models.ForeignKey(NormalizedRecord, on_delete=models.PROTECT, related_name='reviews', db_index=True)
    analyst = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reviews')
    
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    previous_state = models.CharField(max_length=30)
    new_state = models.CharField(max_length=30)
    notes = models.TextField(help_text="Detailed context or explanation of the certification decision or dispute.")
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'review_decisions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analyst.username} action {self.action_type} on {self.normalized_record_id}"


class AuditEvent(models.Model):
    """
    Maintains an immutable, chronologically-chained record of all system state transitions
    and administrative freezes for compliance verification.
    This model is strictly write-once (immutable).
    """
    ACTION_TYPES = [
        ('RECORD_INGESTED', 'Raw Ingestion Job Completed'),
        ('METRIC_RECALCULATED', 'Recalculation and Factor Update'),
        ('METRIC_APPROVED', 'Analyst Approved Metric'),
        ('PERIOD_LOCKED', 'Reporting Period Frozen'),
        ('LEDGER_VERIFIED', 'System Integrity Checked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='audit_events', db_index=True)
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='audit_events')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, db_index=True)
    
    payload_snapshot = models.JSONField(help_text="Stores the serialized properties of modified elements or lock contexts.")
    
    action_timestamp = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)

    class Meta:
        db_table = 'audit_events'
        ordering = ['-action_timestamp']

    def __str__(self):
        return f"{self.action_type} - {self.action_timestamp}"
