from celery import shared_task
import time
import logging
from django.utils import timezone
from .models import Analysis, Artifact
from apps.cases.models import Evidence
from .ai_service import AICopilotService

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def start_evidence_analysis(self, analysis_id, options=None):
    """
    Background task to orchestrate forensic analysis (Pillar 3).
    """
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.started_at = timezone.now()
        analysis.save()

        ai_service = AICopilotService()

        # Step 1: File system parsing (Mock)
        analysis.progress_percent = 10.0
        analysis.save()
        _create_mock_artifacts(analysis, ai_service)

        # Step 2: AI Enrichment
        analysis.progress_percent = 70.0
        analysis.save()
        # (AI enrichment happens during artifact creation in this mock)

        analysis.status = 'completed'
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
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()
        except Exception:
            pass
        return f"Failed: {str(e)}"


def _create_mock_artifacts(analysis, ai_service):
    """Generates mock artifacts and enriched with AI"""
    
    mock_data = [
        {
            'type': 'chat',
            'name': 'WhatsApp Message from +12345',
            'content': 'Meeting for Project X at 2 PM. Don\'t tell anyone.',
            'metadata': {'app': 'WhatsApp', 'sender': '+12345'}
        },
        {
            'type': 'file',
            'name': 'mimikatz.exe',
            'content': 'Binary data...',
            'metadata': {'entropy': 7.9, 'path': '/tmp/mimikatz.exe'}
        },
        {
            'type': 'browser_history',
            'name': 'Google Search: how to delete logs',
            'content': 'Search query: how to delete system logs silently',
            'metadata': {'browser': 'Chrome', 'url': 'google.com'}
        }
    ]

    for item in mock_data:
        # AI Anomaly Detection
        ai_analysis = ai_service.identify_anomalies(item['metadata'])
        
        Artifact.objects.create(
            evidence=analysis.evidence,
            analysis=analysis,
            type=item['type'],
            name=item['name'],
            content=item['content'],
            metadata=item['metadata'],
            ai_labels=ai_analysis['reasons'],
            is_suspicious=ai_analysis['is_suspicious'],
            risk_score=ai_analysis['risk_score'],
            timestamp=timezone.now()
        )
