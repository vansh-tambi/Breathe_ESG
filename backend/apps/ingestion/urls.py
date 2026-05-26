from django.urls import path
from apps.ingestion.views import SAPIngestionView, UtilityIngestionView

app_name = 'ingestion'

urlpatterns = [
    path('sap-upload/', SAPIngestionView.as_view(), name='sap_upload'),
    path('utility-upload/', UtilityIngestionView.as_view(), name='utility_upload'),
]
