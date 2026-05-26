from rest_framework import serializers
from apps.normalization.models import NormalizedRecord, ReviewDecision

class NormalizedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormalizedRecord
        fields = [
            'id',
            'activity_type',
            'scope_classification',
            'reporting_date',
            'raw_quantity',
            'raw_unit',
            'normalized_quantity',
            'normalized_unit',
            'review_status',
            'is_locked',
            # Travel specific fields
            'travel_category',
            'origin_airport_code',
            'destination_airport_code',
            'distance_km',
        ]
        read_only_fields = fields

class ReviewActionSerializer(serializers.Serializer):
    normalized_record_id = serializers.UUIDField()
    analyst_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    notes = serializers.CharField(style={'base_template': 'textarea.html'}, required=False, allow_blank=True)
