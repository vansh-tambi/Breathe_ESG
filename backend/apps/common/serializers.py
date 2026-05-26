from rest_framework import serializers

class BaseIngestionSerializer(serializers.Serializer):
    """
    Base serializer for handling file uploads, validating CSV type and data source parameter.
    """
    data_source_id = serializers.UUIDField()
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV formatted data exports are supported.")
        return value
