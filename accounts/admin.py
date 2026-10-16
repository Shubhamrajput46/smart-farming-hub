from django.contrib import admin

from .models import ActivityLog, FarmerDocument, FarmerProfile


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'farmer_id_code', 'phone', 'village', 'district', 'is_verified')
    search_fields = ('full_name', 'phone', 'village')
    list_filter = ('is_verified', 'state')


admin.site.register(FarmerDocument)
admin.site.register(ActivityLog)
