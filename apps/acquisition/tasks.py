from celery import shared_task
import logging
from .models import AcquisitionTask
from .physical import PhysicalImager

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def run_acquisition(self, task_id):
    """
    Background task to execute forensic acquisition.
    router logic to select the correct imager based on task type.
    """
    try:
        task = AcquisitionTask.objects.get(id=task_id)
        
        logger.info(f"Starting acquisition task {task_id} of type {task.type}")
        
        if task.type in ['disk_physical', 'disk_expert']:
            imager = PhysicalImager(task)
            success = imager.acquire()
        elif task.type == 'memory_dump':
            # Placeholder for Volatility imager
            task.status = 'failed'
            task.error_message = "Memory acquisition not yet implemented"
            task.save()
            return "Memory acquisition not implemented"
        else:
            task.status = 'failed' 
            task.error_message = f"Unsupported acquisition type: {task.type}"
            task.save()
            return f"Unsupported type: {task.type}"

        return "Acquisition completed successfully" if success else "Acquisition failed"

    except AcquisitionTask.DoesNotExist:
        logger.error(f"AcquisitionTask {task_id} not found")
        return "Task not found"
    except Exception as e:
        logger.error(f"Critical error in acquisition task: {e}")
        return f"Critical error: {e}"
