from rest_framework import serializers
from apps.ingestion.models import DataSource
from apps.common.serializers import BaseIngestionSerializer

class SAPIngestionSerializer(BaseIngestionSerializer):
    """
    Validates SAP procurement file uploads.
    """
    def validate_data_source_id(self, value):
        try:
            source = DataSource.objects.get(id=value, is_active=True)
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Active data source not found.")
            
        if source.source_type != 'SAP_PROCUREMENT':
            raise serializers.ValidationError("Target data source must be configured for SAP exports ingestion.")
        return source


class TravelIngestionSerializer(BaseIngestionSerializer):
    """
    Validates corporate travel file uploads.
    """
    def validate_data_source_id(self, value):
        try:
            source = DataSource.objects.get(id=value, is_active=True)
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Active data source not found.")
            
        if source.source_type != 'TRAVEL_CONCUR':
            raise serializers.ValidationError("Target data source must be configured for Travel Concur ingestion.")
        return source


class UtilityIngestionSerializer(BaseIngestionSerializer):
    """
    Validates utility portal energy file uploads.
    """
    def validate_data_source_id(self, value):
        try:
            source = DataSource.objects.get(id=value, is_active=True)
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Active data source not found.")
            
        if source.source_type != 'UTILITY_PORTAL':
            raise serializers.ValidationError("Target data source must be configured for Utility Portal ingestion.")
        return source
