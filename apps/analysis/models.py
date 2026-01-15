from django.db import models
from django.utils import timezone
import uuid
from apps.cases.models import Evidence

class Analysis(models.Model):
    """Pillar 3: AI-Powered Analysis Suite"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='analyses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percent = models.FloatField(default=0.0)
    
    # Analysis Configuration
    use_ai = models.BooleanField(default=True)
    extract_artifacts = models.BooleanField(default=True)
    index_for_search = models.BooleanField(default=True)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Analyses"

    def __str__(self):
        return f"Analysis on {self.evidence.name} ({self.status})"


class Artifact(models.Model):
    """Extracted digital evidence items"""
    ARTIFACT_TYPES = [
        ('file', 'File'),
        ('email', 'Email'),
        ('chat', 'Chat Message'),
        ('call_log', 'Call Log'),
        ('browser_history', 'Browser History'),
        ('registry', 'System Registry'),
        ('log', 'System Log'),
        ('location', 'Location Data'),
        ('media', 'Media (Image/Video)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='artifacts')
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='artifacts')
    
    type = models.CharField(max_length=50, choices=ARTIFACT_TYPES)
    name = models.CharField(max_length=512)
    original_path = models.TextField(blank=True)
    
    # Content and Metadata
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # AI Enrichment
    ai_labels = models.JSONField(default=list, blank=True)  # Objects detected, intent analysis, etc.
    ai_summary = models.TextField(blank=True)
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.FloatField(default=0.0)
    
    # Timestamps from evidence
    timestamp = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.type}: {self.name}"
