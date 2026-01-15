from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.cases.models import Case, Evidence, AuditLog
from .middleware import get_current_user

User = get_user_model()

def log_action(instance, action, details):
    user = get_current_user()
    
    # If no user in context (e.g. background task), try to find a system user or use None
    if not user:
        # Check if instance has a user field relevant to creation
        if hasattr(instance, 'created_by') and action == 'Created':
            user = instance.created_by
        elif hasattr(instance, 'acquired_by') and action == 'Created':
             user = instance.acquired_by
    
    # Resolve Case reference
    case = None
    if isinstance(instance, Case):
        case = instance
    elif isinstance(instance, Evidence):
        case = instance.case
        
    if case:
        AuditLog.objects.create(
            case=case,
            user=user,
            action=f"{instance.__class__.__name__} {action}",
            details=details
        )

@receiver(post_save, sender=Case)
@receiver(post_save, sender=Evidence)
def log_save(sender, instance, created, **kwargs):
    action = 'Created' if created else 'Updated'
    
    # Basic diff logic could go here for updates
    details = {
        'id': str(instance.id),
        'name': getattr(instance, 'name', 'N/A')
    }
    
    log_action(instance, action, details)

@receiver(post_delete, sender=Case)
@receiver(post_delete, sender=Evidence)
def log_delete(sender, instance, **kwargs):
    details = {
        'id': str(instance.id),
        'name': getattr(instance, 'name', 'N/A')
    }
    log_action(instance, 'Deleted', details)
