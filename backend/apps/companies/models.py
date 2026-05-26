import uuid
from django.db import models

class Company(models.Model):
    """
    Represents an independent enterprise tenant. Acts as the root partition for multi-tenancy.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    domain_prefix = models.CharField(max_length=63, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    
    # Justification: Needed by operations and compliance to track client onboarding timelines.
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    
    # Justification: Needed to audit administrative configuration changes to tenant parameters.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name
