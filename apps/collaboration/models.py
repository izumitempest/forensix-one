from django.db import models
from django.contrib.auth import get_user_model
import uuid
from apps.cases.models import Case

User = get_user_model()

class Role(models.Model):
    """Pillar 6: Granular permissions/roles"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Permissions (Simplified)
    can_acquire = models.BooleanField(default=False)
    can_analyze = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    can_admin_case = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class CaseParticipant(models.Model):
    """Links users to cases with specific roles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_participations')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('case', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.case.name}"

class CaseNote(models.Model):
    """Real-time note sharing between analysts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    content = models.TextField()
    parent_note = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.author.username} on {self.created_at}"
