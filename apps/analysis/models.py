from django.db import models
from django.utils import timezone
import uuid
from apps.cases.models import Evidence


class Analysis(models.Model):
    """Pillar 3: AI-Powered Analysis Suite"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    ENGINE_CHOICES = [
        ("basic_metadata", "Basic Metadata Extractor"),
        ("deep_file", "Deep File Content Analysis"),
        ("ai_copilot", "AI Copilot Semantic Search"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(
        Evidence, on_delete=models.CASCADE, related_name="analyses"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    type = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="basic_metadata"
    )
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

    @property
    def overall_risk_score(self):
        """Returns the maximum risk score among all artifacts in this analysis"""
        max_risk = self.artifacts.aggregate(models.Max("risk_score"))["risk_score__max"]
        return max_risk or 0.0

    class Meta:
        verbose_name_plural = "Analyses"

    def __str__(self):
        return f"Analysis on {self.evidence.name} ({self.status})"


class Artifact(models.Model):
    """Extracted digital evidence items"""

    ARTIFACT_TYPES = [
        ("file", "File"),
        ("email", "Email"),
        ("chat", "Chat Message"),
        ("call_log", "Call Log"),
        ("browser_history", "Browser History"),
        ("registry", "System Registry"),
        ("log", "System Log"),
        ("location", "Location Data"),
        ("media", "Media (Image/Video)"),
        ("browser_cookie", "Browser Cookie"),
        ("browser_download", "Browser Download"),
        ("windows_lnk", "Windows LNK Link File"),
        ("prefetch_file", "Windows Prefetch"),
        ("shellbag", "Windows Shellbag"),
        ("usn_journal", "NTFS USN Journal Entry"),
        ("metadata_exif", "EXIF Metadata"),
        ("metadata_ole", "OLE/Document Metadata"),
        ("network_flow", "Network Connection"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(
        Evidence, on_delete=models.CASCADE, related_name="artifacts"
    )
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="artifacts"
    )

    type = models.CharField(max_length=50, choices=ARTIFACT_TYPES)
    name = models.CharField(max_length=512)
    original_path = models.TextField(blank=True)

    # Content and Metadata
    content = models.TextField(blank=True)
    raw_hex_preview = models.TextField(
        blank=True, help_text="Hex dump of relevant bytes"
    )
    metadata = models.JSONField(default=dict)
    file_system_metadata = models.JSONField(default=dict, blank=True)

    # AI Enrichment
    ai_labels = models.JSONField(
        default=list, blank=True
    )  # Objects detected, intent analysis, etc.
    ai_summary = models.TextField(blank=True)
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.FloatField(default=0.0)

    # Timestamps from evidence
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["is_suspicious"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.type}: {self.name}"
