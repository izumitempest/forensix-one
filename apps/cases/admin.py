from django.contrib import admin
from .models import Case, Evidence, AuditLog, CaseTag

@admin.register(CaseTag)
class CaseTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'name', 'status', 'priority', 'case_type', 'created_at')
    list_filter = ('status', 'priority', 'case_type')
    search_fields = ('name', 'case_number', 'description')
    readonly_fields = ('case_number', 'created_at', 'updated_at')
    filter_horizontal = ('assigned_to', 'tags')

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'case', 'size_bytes', 'acquisition_date')
    list_filter = ('source_type', 'case')
    search_fields = ('name', 'md5_hash', 'sha256_hash')
    readonly_fields = ('created_at',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'case', 'user', 'action', 'ip_address')
    list_filter = ('case', 'user', 'action')
    search_fields = ('action', 'details')
    readonly_fields = ('timestamp',)
