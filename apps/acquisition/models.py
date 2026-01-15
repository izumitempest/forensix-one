from django.db import models
import uuid
from apps.cases.models import Evidence
from django.contrib.auth import get_user_model

User = get_user_model()

class AcquisitionTask(models.Model):
    """Pillar 1: Universal Acquisition Engine - Tracking"""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    ACQUISITION_TYPES = [
        ('disk_physical', 'Physical Disk (DD)'),
        ('disk_expert', 'Expert Witness (E01)'),
        ('memory_dump', 'Memory Dump'),
        ('mobile_ios', 'iOS Extraction'),
        ('mobile_android', 'Android Extraction'),
        ('cloud_s3', 'Cloud S3 Capture'),
        ('network_pcap', 'Network PCAP'),
        ('remote_agent', 'Remote Agent Collection'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name='acquisition_task', null=True)
    
    type = models.CharField(max_length=50, choices=ACQUISITION_TYPES)
    source_path = models.CharField(max_length=1024)
    destination_path = models.CharField(max_length=1024)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress_percent = models.FloatField(default=0.0)
    current_speed = models.CharField(max_length=50, blank=True) # MB/s
    
    # Forensic data
    calculated_md5 = models.CharField(max_length=32, blank=True)
    calculated_sha256 = models.CharField(max_length=64, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Logs/Error
    logs = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.status}"
