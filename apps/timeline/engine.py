import logging
from .models import TimelineEvent
from apps.analysis.models import Artifact
from django.db import transaction

logger = logging.getLogger(__name__)

class TimelineCorrelationEngine:
    """
    Pillar 5: Intelligent Timeline Engine - Correlation Logic
    Links events across devices, apps, and sources automatically.
    """
    
    @staticmethod
    @transaction.atomic
    def correlate_artifacts_to_timeline(analysis):
        """
        Parses all artifacts from an analysis and creates timeline events.
        """
        artifacts = Artifact.objects.filter(analysis=analysis)
        events_created = 0
        
        for artifact in artifacts:
            if not artifact.timestamp:
                continue
                
            # Create a base timeline event
            event = TimelineEvent.objects.create(
                case=analysis.evidence.case,
                evidence=analysis.evidence,
                artifact=artifact,
                timestamp=artifact.timestamp,
                event_type=artifact.type,
                source_type='application',
                description=f"{artifact.get_type_display()}: {artifact.name}",
                context_data=artifact.metadata
            )
            
            # Auto-correlation: If it's a chat message, try to link with location data
            if artifact.type == 'chat':
                TimelineCorrelationEngine._correlate_chat_with_location(event)
                
            events_created += 1
            
        return events_created

    @staticmethod
    def _correlate_chat_with_location(chat_event):
        """
        Attempt to find location data near the chat timestamp for multi-source overlay.
        """
        # Search for location events within a 5-minute window
        # This is a placeholder for spatial-temporal correlation logic
        pass

    @staticmethod
    def identify_timeline_gaps(case):
        """
        Identifies suspicious temporal gaps where no activity was recorded.
        Helps detect potential data destruction.
        """
        events = TimelineEvent.objects.filter(case=case).order_by('timestamp')
        if events.count() < 2:
            return []
            
        gaps = []
        prev_event = events[0]
        
        for i in range(1, len(events)):
            current_event = events[i]
            diff = current_event.timestamp - prev_event.timestamp
            
            # If gap is larger than 24 hours without any events
            if diff.total_seconds() > 86400:
                gaps.append({
                    'start_time': prev_event.timestamp,
                    'end_time': current_event.timestamp,
                    'duration': str(diff)
                })
                # Flag events as part of a gap
                prev_event.is_gap_flagged = True
                prev_event.save()
                
            prev_event = current_event
            
        return gaps
