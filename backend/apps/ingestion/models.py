import uuid
from django.db import models
from apps.companies.models import Company

class DataSource(models.Model):
    """
    Defines the configured integrations or file sources from which activity data is ingested.
    """
    SOURCE_TYPES = [
        ('SAP_PROCUREMENT', 'SAP Fuel and Procurement'),
        ('UTILITY_PORTAL', 'Electricity Utility Portal'),
        ('TRAVEL_CONCUR', 'Corporate Travel Concur/Navan JSON'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='data_sources', db_index=True)
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    configuration_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores client-specific column mappings, plant code translation tables, or API parameters."
    )
    is_active = models.BooleanField(default=True)
    
    # Justification: Crucial to track when integrations were established or reconfigured.
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'data_sources'
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class RawRecord(models.Model):
    """
    Stores unmodified raw content exactly as received from sources to preserve absolute lineage.
    This model is strictly write-once (immutable).
    """
    STATE_CHOICES = [
        ('UNPROCESSED', 'Unprocessed'),
        ('NORMALIZED', 'Successfully Normalized'),
        ('REJECTED', 'Rejected on Structural Validation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='raw_records', db_index=True)
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='raw_records', db_index=True)
    job_id = models.UUIDField(db_index=True, help_text="Groups all rows imported during the same file transaction.")
    sequence_number = models.IntegerField(help_text="The line index in the source file for precise audit tracking.")
    raw_payload = models.JSONField(help_text="Contains the exact, untranslated JSON or CSV row key-values.")
    processing_state = models.CharField(max_length=30, choices=STATE_CHOICES, default='UNPROCESSED', db_index=True)
    structural_error = models.TextField(null=True, blank=True, help_text="Details structural compilation or column failures.")
    
    # Justification: Needed to prove the legal arrival timestamp of data payloads to regulators.
    # Excluded updated_at: Raw data is immutable; raw values must never be modified once received.
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'raw_records'
        ordering = ['job_id', 'sequence_number']

    def __str__(self):
        return f"RawRecord Job {self.job_id} Line {self.sequence_number}"


class PlantLookup(models.Model):
    """
    Tenant-specific SAP plant mappings to physical facilities and emission grid regions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='plant_lookups', db_index=True)
    sap_plant_code = models.CharField(max_length=50, db_index=True)
    facility_name = models.CharField(max_length=255)
    grid_region_code = models.CharField(max_length=50, help_text="Used to resolve region-specific Scope 2 grid factors.")
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plant_lookups'
        unique_together = ('company', 'sap_plant_code')

    def __str__(self):
        return f"{self.sap_plant_code} -> {self.facility_name}"
