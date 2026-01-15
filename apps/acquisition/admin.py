from django.contrib import admin
from .models import AcquisitionTask

@admin.register(AcquisitionTask)
class AcquisitionTaskAdmin(admin.ModelAdmin):
    list_display = ('type', 'status', 'progress_percent', 'created_at', 'created_by')
    list_filter = ('type', 'status', 'created_by')
    search_fields = ('source_path', 'destination_path', 'error_message')
    readonly_fields = ('created_at', 'started_at', 'completed_at')
