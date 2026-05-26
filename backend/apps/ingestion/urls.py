from django.urls import path
from apps.ingestion.views import SAPIngestionView, UtilityIngestionView, TravelIngestionView

app_name = 'ingestion'

urlpatterns = [
    path('sap-upload/', SAPIngestionView.as_view(), name='sap_upload'),
    path('utility-upload/', UtilityIngestionView.as_view(), name='utility_upload'),
    path('travel-upload/', TravelIngestionView.as_view(), name='travel_upload'),
]
