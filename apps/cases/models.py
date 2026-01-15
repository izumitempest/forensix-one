from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class CaseTag(models.Model):
    """Tags for categorizing cases"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Case(models.Model):
    """Main case model"""
    CASE_TYPES = [
        ('corporate', 'Corporate Investigation'),
        ('criminal', 'Criminal Investigation'),
        ('civil', 'Civil Litigation'),
        ('internal', 'Internal Investigation'),
        ('incident_response', 'Incident Response'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
        ('on_hold', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=50, unique=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    case_type = models.CharField(max_length=30, choices=CASE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Relationships
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_cases')
    assigned_to = models.ManyToManyField(User, related_name='assigned_cases', blank=True)
    tags = models.ManyToManyField(CaseTag, related_name='cases', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['case_type']),
        ]
    
    def __str__(self):
        return f"{self.case_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.case_number:
            # Generate case number: CASE-YYYY-NNNN
            year = timezone.now().year
            last_case = Case.objects.filter(
                case_number__startswith=f'CASE-{year}'
            ).order_by('-case_number').first()
            
            if last_case:
                last_num = int(last_case.case_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.case_number = f'CASE-{year}-{new_num:04d}'
        
        super().save(*args, **kwargs)
    
    def calculate_analysis_progress(self):
        """Calculate overall analysis progress"""
        from apps.analysis.models import Analysis
        analyses = Analysis.objects.filter(evidence__case=self)
        
        if not analyses.exists():
            return 0.0
        
        total_progress = sum(a.progress_percent or 0 for a in analyses)
        return round(total_progress / analyses.count(), 2)


class Evidence(models.Model):
    """Evidence linked to a case"""
    SOURCE_TYPES = [
        ('disk', 'Disk Image'),
        ('memory', 'Memory Dump'),
        ('mobile', 'Mobile Extraction'),
        ('cloud', 'Cloud Capture'),
        ('network', 'Network Capture'),
        ('live', 'Live Forensic Capture'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='evidence')
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    
    # Storage
    file_path = models.CharField(max_length=1024)  # Path to image/extraction
    size_bytes = models.BigIntegerField()
    
    # Forensic Soundness
    md5_hash = models.CharField(max_length=32, blank=True)
    sha256_hash = models.CharField(max_length=64, blank=True)
    acquisition_date = models.DateTimeField(default=timezone.now)
    acquisition_method = models.CharField(max_length=100)
    acquired_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='acquired_evidence')
    
    # Metadata
    device_info = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Evidence"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class AuditLog(models.Model):
    """Pillar 6: Forensic Audit Trail"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Chain of custody
    blockchain_tx_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
