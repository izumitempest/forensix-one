from django.contrib import admin
from .models import Report, ReportTemplate

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_system')
    search_fields = ('name', 'description')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'case', 'format', 'created_at', 'created_by')
    list_filter = ('format', 'case', 'created_by')
    search_fields = ('name', 'generated_content')
    readonly_fields = ('created_at',)
