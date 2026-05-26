from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.common.permissions import IsAuthenticatedOrLocal
from apps.normalization.models import NormalizedRecord, ReviewDecision
from apps.normalization.serializers import NormalizedRecordSerializer, ReviewDecisionSerializer

User = get_user_model()

def get_mock_analyst():
    """
    Get or create a mock analyst user for compliance actions auditing in local testing.
    """
    analyst = User.objects.first()
    if not analyst:
        analyst = User.objects.create_user(username='mock_analyst', password='password123')
    return analyst


class RecordsView(APIView):
    permission_classes = [IsAuthenticatedOrLocal]

    def get(self, request, *args, **kwargs):
        company_id = request.query_params.get('company_id')
        records = NormalizedRecord.objects.filter(company_id=company_id)
        serializer = NormalizedRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuspiciousView(APIView):
    permission_classes = [IsAuthenticatedOrLocal]

    def get(self, request, *args, **kwargs):
        company_id = request.query_params.get('company_id')
        records = NormalizedRecord.objects.filter(company_id=company_id, review_status='SUSPICIOUS')
        serializer = NormalizedRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuditLogView(APIView):
    permission_classes = [IsAuthenticatedOrLocal]

    def get(self, request, *args, **kwargs):
        company_id = request.query_params.get('company_id')
        decisions = ReviewDecision.objects.filter(company_id=company_id)
        serializer = ReviewDecisionSerializer(decisions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApproveRecordView(APIView):
    permission_classes = [IsAuthenticatedOrLocal]

    def post(self, request, *args, **kwargs):
        record_id = request.data.get('record_id')
        notes = request.data.get('notes', '')
        company_id = request.query_params.get('company_id')

        try:
            record = NormalizedRecord.objects.get(id=record_id, company_id=company_id)
            if record.is_locked:
                return Response({"error": "Cannot modify locked record"}, status=status.HTTP_400_BAD_REQUEST)

            previous_state = record.review_status
            record.review_status = 'APPROVED'
            record.save()

            ReviewDecision.objects.create(
                company_id=company_id,
                normalized_record=record,
                analyst=get_mock_analyst(),
                action_type='APPROVE',
                previous_state=previous_state,
                new_state='APPROVED',
                notes=notes
            )
            return Response({"status": "approved"}, status=status.HTTP_200_OK)
        except NormalizedRecord.DoesNotExist:
            return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)


class RejectRecordView(APIView):
    permission_classes = [IsAuthenticatedOrLocal]

    def post(self, request, *args, **kwargs):
        record_id = request.data.get('record_id')
        notes = request.data.get('notes', '')
        company_id = request.query_params.get('company_id')

        try:
            record = NormalizedRecord.objects.get(id=record_id, company_id=company_id)
            if record.is_locked:
                return Response({"error": "Cannot modify locked record"}, status=status.HTTP_400_BAD_REQUEST)

            previous_state = record.review_status
            record.review_status = 'DISPUTED'
            record.save()

            ReviewDecision.objects.create(
                company_id=company_id,
                normalized_record=record,
                analyst=get_mock_analyst(),
                action_type='DISPUTE',
                previous_state=previous_state,
                new_state='DISPUTED',
                notes=notes
            )
            return Response({"status": "rejected"}, status=status.HTTP_200_OK)
        except NormalizedRecord.DoesNotExist:
            return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)


class LockRecordView(APIView):
    permission_classes = [IsAuthenticatedOrLocal]

    def post(self, request, *args, **kwargs):
        record_id = request.data.get('record_id')
        notes = request.data.get('notes', '')
        company_id = request.query_params.get('company_id')

        try:
            record = NormalizedRecord.objects.get(id=record_id, company_id=company_id)
            if record.is_locked:
                return Response({"error": "Record is already locked"}, status=status.HTTP_400_BAD_REQUEST)

            previous_state = record.review_status
            record.review_status = 'LOCKED'
            record.is_locked = True
            record.save()

            ReviewDecision.objects.create(
                company_id=company_id,
                normalized_record=record,
                analyst=get_mock_analyst(),
                action_type='LOCK',
                previous_state=previous_state,
                new_state='LOCKED',
                notes=notes
            )
            return Response({"status": "locked"}, status=status.HTTP_200_OK)
        except NormalizedRecord.DoesNotExist:
            return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
