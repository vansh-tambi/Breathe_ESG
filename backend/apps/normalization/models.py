import uuid
from django.db import models
from apps.companies.models import Company
from apps.ingestion.models import RawRecord

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
    
    # Calculation Audit Details
    emission_factor_applied = models.DecimalField(max_digits=18, decimal_places=8)
    co2e_metric_tons = models.DecimalField(max_digits=18, decimal_places=6)
    
    # Administrative & Verification Status
    review_status = models.CharField(max_length=30, choices=REVIEW_STATUS_CHOICES, default='PENDING_REVIEW', db_index=True)
    is_locked = models.BooleanField(default=False, db_index=True)
    
    # Justification: Crucial for calculating metric generation latency.
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    
    # Justification: Crucial to track recalculations or review transitions.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'normalized_records'
        ordering = ['-reporting_date']

    def __str__(self):
        return f"{self.activity_type} on {self.reporting_date}: {self.co2e_metric_tons} tCO2e"
