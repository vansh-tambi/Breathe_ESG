from django.urls import path
from apps.normalization.views import (
    RecordsView, SuspiciousView, AuditLogView,
    ApproveRecordView, RejectRecordView, LockRecordView
)

app_name = 'normalization'

urlpatterns = [
    path('records/', RecordsView.as_view(), name='records'),
    path('suspicious/', SuspiciousView.as_view(), name='suspicious'),
    path('audit/', AuditLogView.as_view(), name='audit'),
    path('approve/', ApproveRecordView.as_view(), name='approve'),
    path('reject/', RejectRecordView.as_view(), name='reject'),
    path('lock/', LockRecordView.as_view(), name='lock'),
]
