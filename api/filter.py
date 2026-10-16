"""Optional django-filter filters for the AgroSmart API."""
import django_filters
from farms.models import Crop
from ai_services.models import MandiPrice

class CropFilter(django_filters.FilterSet):
    class Meta:
        model = Crop
        fields = {}  # Add only fields that exist in your Crop model.

class MandiPriceFilter(django_filters.FilterSet):
    # Filters are intentionally not declared until the exact model field names are verified.
    class Meta:
        model = MandiPrice
        fields = {}
        filterset_fields = ["state", "district", "market"]
