from django.contrib import admin

from .models import Crop, CropOperationLog, Land


@admin.register(Land)
class LandAdmin(admin.ModelAdmin):
    list_display = ('title', 'farmer', 'total_area_acres', 'soil_type', 'ownership')
    list_filter = ('soil_type', 'ownership')


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('name', 'land', 'season', 'allocated_acres', 'stage', 'expected_harvest_date')
    list_filter = ('stage', 'season')
    search_fields = ('name',)


@admin.register(CropOperationLog)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('crop', 'operation_type', 'date', 'total_cost')
    list_filter = ('operation_type',)
