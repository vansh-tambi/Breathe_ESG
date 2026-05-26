import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.normalization.models import NormalizedRecord

User = get_user_model()

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
    
    # Justification: Crucial to record the exact historical timestamp of analyst decisions.
    # Excluded updated_at: Decisions are write-once logs; analyst decisions must never be modified retrospectively.
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'review_decisions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analyst.username} action {self.action_type} on {self.normalized_record_id}"
