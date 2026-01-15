from django.db import models
import uuid
from apps.cases.models import Case
from django.contrib.auth import get_user_model

User = get_user_model()

class ReportTemplate(models.Model):
    """Templates for different types of reports"""
    name = models.CharField(max_length=255)
    description = models.TextField()
    html_template = models.TextField()
    is_system = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Report(models.Model):
    """Pillar 4: Smart Reporting & Export"""
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('html', 'HTML'),
        ('case', 'CASE (Standard Expression)'),
        ('json', 'JSON'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True)
    
    name = models.CharField(max_length=255)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    
    # Content
    generated_content = models.TextField(blank=True) # AI-assisted narratives
    file_path = models.CharField(max_length=1024, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Security
    digital_signature = models.TextField(blank=True)
    blockchain_proof = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.format.upper()})"
