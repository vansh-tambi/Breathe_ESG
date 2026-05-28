from rest_framework import serializers
from apps.companies.models import Company
from apps.ingestion.models import DataSource
from apps.common.serializers import BaseIngestionSerializer

class SAPIngestionSerializer(BaseIngestionSerializer):
    """
    Validates SAP procurement file uploads.
    """
    def validate_data_source_id(self, value):
        company, _ = Company.objects.get_or_create(
            domain_prefix='demo',
            defaults={
                'id': '00000000-0000-0000-0000-000000000001',
                'name': 'Demo Tenant'
            }
        )
        source, _ = DataSource.objects.get_or_create(
            id=value,
            defaults={
                'company': company,
                'name': f'Auto-created SAP Source {str(value)[:8]}',
                'source_type': 'SAP_PROCUREMENT',
                'is_active': True
            }
        )

        if source.source_type != 'SAP_PROCUREMENT':
            raise serializers.ValidationError("Target data source must be configured for SAP exports ingestion.")
        return source


class TravelIngestionSerializer(BaseIngestionSerializer):
    """
    Validates corporate travel file uploads.
    """
    def validate_data_source_id(self, value):
        company, _ = Company.objects.get_or_create(
            domain_prefix='demo',
            defaults={
                'id': '00000000-0000-0000-0000-000000000001',
                'name': 'Demo Tenant'
            }
        )
        source, _ = DataSource.objects.get_or_create(
            id=value,
            defaults={
                'company': company,
                'name': f'Auto-created Travel Source {str(value)[:8]}',
                'source_type': 'TRAVEL_CONCUR',
                'is_active': True
            }
        )

        if source.source_type != 'TRAVEL_CONCUR':
            raise serializers.ValidationError("Target data source must be configured for Travel Concur ingestion.")
        return source


class UtilityIngestionSerializer(BaseIngestionSerializer):
    """
    Validates utility portal energy file uploads.
    """
    def validate_data_source_id(self, value):
        company, _ = Company.objects.get_or_create(
            domain_prefix='demo',
            defaults={
                'id': '00000000-0000-0000-0000-000000000001',
                'name': 'Demo Tenant'
            }
        )
        source, _ = DataSource.objects.get_or_create(
            id=value,
            defaults={
                'company': company,
                'name': f'Auto-created Utility Source {str(value)[:8]}',
                'source_type': 'UTILITY_PORTAL',
                'is_active': True
            }
        )

        if source.source_type != 'UTILITY_PORTAL':
            raise serializers.ValidationError("Target data source must be configured for Utility Portal ingestion.")
        return source

