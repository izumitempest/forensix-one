from django.contrib import admin
from .models import Analysis, Artifact

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('evidence', 'status', 'progress_percent', 'started_at', 'completed_at')
    list_filter = ('status', 'use_ai', 'extract_artifacts')
    readonly_fields = ('started_at', 'completed_at', 'progress_percent')

@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'evidence', 'is_suspicious', 'risk_score', 'timestamp')
    list_filter = ('type', 'is_suspicious', 'evidence')
    search_fields = ('name', 'content', 'original_path')
    readonly_fields = ('timestamp',)
