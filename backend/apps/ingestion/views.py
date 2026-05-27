from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
import logging
from apps.ingestion.serializers import SAPIngestionSerializer, UtilityIngestionSerializer
from apps.ingestion.services.travel_pipeline import process_travel_csv
from apps.ingestion.services.sap_pipeline import process_sap_csv
from apps.ingestion.services.utility_pipeline import process_utility_csv

logger = logging.getLogger(__name__)

class SAPIngestionView(APIView):
    """
    Receives SAP CSV file uploads and triggers the transactional normalization pipeline.
    """
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SAPIngestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data_source = serializer.validated_data['data_source_id']
        csv_file = serializer.validated_data['file']
        
        company = data_source.company

        try:
            summary = process_sap_csv(
                company=company,
                data_source=data_source,
                file_handle=csv_file
            )
            return Response(summary, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("SAP Ingestion failed: %s", str(e), exc_info=True)
            raise ValidationError({"error": "Pipeline processing failed", "details": str(e)})


class UtilityIngestionView(APIView):
    """
    Receives Utility CSV uploads and runs standard conversions, splitting dates pro-rata.
    """
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UtilityIngestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data_source = serializer.validated_data['data_source_id']
        csv_file = serializer.validated_data['file']
        
        company = data_source.company

        try:
            summary = process_utility_csv(
                company=company,
                data_source=data_source,
                file_handle=csv_file
            )
            return Response(summary, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Utility Ingestion failed: %s", str(e), exc_info=True)
            raise ValidationError({"error": "Pipeline processing failed", "details": str(e)})

class TravelIngestionView(APIView):
    """
    Receives Concur-style travel CSV uploads and processes travel records.
    """
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from apps.ingestion.serializers import TravelIngestionSerializer
        serializer = TravelIngestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data_source = serializer.validated_data['data_source_id']
        csv_file = serializer.validated_data['file']
        company = data_source.company

        try:
            summary = process_travel_csv(
                company=company,
                data_source=data_source,
                file_handle=csv_file
            )
            return Response(summary, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Travel Ingestion failed: %s", str(e), exc_info=True)
            raise ValidationError({"error": "Pipeline processing failed", "details": str(e)})
