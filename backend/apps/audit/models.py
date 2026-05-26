import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

class AuditEvent(models.Model):
    """
    Maintains an immutable, chronologically-chained tamper-evident record of all system state transitions
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
    ledger_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash chaining this event back to the company's previous sequential audit log entry."
    )
    
    # Justification: The foundational metric for compliance timelines and regulatory checks.
    # Excluded updated_at: Audit logs are strictly immutable and cannot support administrative alterations.
    action_timestamp = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)

    class Meta:
        db_table = 'audit_events'
        ordering = ['-action_timestamp']

    def __str__(self):
        return f"{self.action_type} - {self.action_timestamp}"
