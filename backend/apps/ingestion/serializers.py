from rest_framework import serializers
from apps.ingestion.models import DataSource

class SAPIngestionSerializer(serializers.Serializer):
    """
    Validates the incoming multipart file and checks active integration mappings for SAP.
    """
    data_source_id = serializers.UUIDField()
    file = serializers.FileField()

    def validate_data_source_id(self, value):
        try:
            source = DataSource.objects.get(id=value, is_active=True)
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Active data source not found.")
            
        if source.source_type != 'SAP_PROCUREMENT':
            raise serializers.ValidationError("Target data source must be configured for SAP exports ingestion.")
        return source

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV formatted data exports are supported.")
        return value


class TravelIngestionSerializer(serializers.Serializer):
    """
    Validates incoming Concur-style travel CSV files and matches travel configurations.
    """
    data_source_id = serializers.UUIDField()
    file = serializers.FileField()

    def validate_data_source_id(self, value):
        try:
            source = DataSource.objects.get(id=value, is_active=True)
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Active data source not found.")
        if source.source_type != 'TRAVEL_CONCUR':
            raise serializers.ValidationError("Target data source must be configured for Travel Concur ingestion.")
        return source

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV formatted data exports are supported.")
        return value
    """
    Validates incoming utility portal CSV files and matches utility configurations.
    """
    data_source_id = serializers.UUIDField()
    file = serializers.FileField()

    def validate_data_source_id(self, value):
        try:
            source = DataSource.objects.get(id=value, is_active=True)
        except DataSource.DoesNotExist:
            raise serializers.ValidationError("Active data source not found.")
            
        if source.source_type != 'UTILITY_PORTAL':
            raise serializers.ValidationError("Target data source must be configured for Utility Portal ingestion.")
        return source

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV formatted data exports are supported.")
        return value
