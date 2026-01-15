from django.contrib import admin
from .models import TimelineEvent

@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'event_type', 'source_type', 'case')
    list_filter = ('event_type', 'source_type', 'case', 'is_gap_flagged')
    search_fields = ('description', 'correlation_id')
    readonly_fields = ('timestamp',)
