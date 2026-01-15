from django.db import models
import uuid
from apps.cases.models import Case, Evidence
from apps.analysis.models import Artifact

class TimelineEvent(models.Model):
    """Pillar 5: Intelligent Timeline Engine"""
    EVENT_SOURCES = [
        ('system', 'System File'),
        ('application', 'Application Data'),
        ('network', 'Network Activity'),
        ('manual', 'Manual Entry'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='timeline_events')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='timeline_events', null=True)
    artifact = models.ForeignKey(Artifact, on_delete=models.SET_NULL, null=True, related_name='timeline_events')
    
    timestamp = models.DateTimeField()
    event_type = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20, choices=EVENT_SOURCES)
    
    description = models.TextField()
    context_data = models.JSONField(default=dict, blank=True)
    
    # Auto-correlation data
    correlation_id = models.CharField(max_length=100, blank=True)
    is_gap_flagged = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.event_type}: {self.description[:50]}"
