from django.urls import path
from apps.ingestion.views import SAPIngestionView

app_name = 'ingestion'

urlpatterns = [
    path('sap-upload/', SAPIngestionView.as_view(), name='sap_upload'),
]
