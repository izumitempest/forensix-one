from celery import shared_task
import time
import logging
from django.utils import timezone
from .models import Analysis, Artifact
from apps.cases.models import Evidence
from .ai_service import AICopilotService
from .engine import MetadataExtractor, ContentScanner, AISummarizer

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def start_evidence_analysis(self, analysis_id, options=None):
    """
    Background task to orchestrate forensic analysis (Pillar 3).
    """
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.status = "processing"
        analysis.started_at = timezone.now()
        analysis.save()

        ai_service = AICopilotService()

        # Step 1: Deep Metadata Extraction (Layer 1 & 2)
        analysis.progress_percent = 5.0
        analysis.save()

        extractor = MetadataExtractor(analysis_id)
        success = extractor.process()

        if not success:
            return f"Analysis {analysis_id} failed during metadata extraction."

        analysis.progress_percent = 50.0
        analysis.save()

        scanner = ContentScanner(analysis_id)
        scanner.process()

        # Step 3: AI Enrichment (Layer 4)
        analysis.progress_percent = 80.0
        analysis.save()

        summarizer = AISummarizer(analysis_id)
        summarizer.process()

        analysis.status = "completed"
        analysis.progress_percent = 100.0
        analysis.completed_at = timezone.now()
        analysis.save()

        return f"Analysis {analysis_id} completed successfully."

    except Analysis.DoesNotExist:
        logger.error("Analysis %s not found.", analysis_id)
        return "Failed: Analysis not found."
    except Exception as e:
        logger.error("Error in evidence analysis: %s", e)
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.save()
        except Exception:
            pass
        return f"Failed: {str(e)}"
