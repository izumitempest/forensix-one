from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import TimelineEvent
from .serializers import TimelineEventSerializer
from .engine import TimelineCorrelationEngine
from rest_framework.decorators import action
from rest_framework.response import Response

class TimelineEventViewSet(viewsets.ModelViewSet):
    queryset = TimelineEvent.objects.all()
    serializer_class = TimelineEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['case', 'event_type', 'source_type', 'is_gap_flagged']
    search_fields = ['description', 'correlation_id']
    ordering_fields = ['timestamp']

    @action(detail=False, methods=['post'], url_path='correlate/(?P<analysis_id>[^/.]+)')
    def correlate(self, request, analysis_id=None):
        """Triggers the correlation engine for a specific analysis"""
        from apps.analysis.models import Analysis
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            events_count = TimelineCorrelationEngine.correlate_artifacts_to_timeline(analysis)
            return Response({'status': 'correlation complete', 'events_created': events_count})
        except Analysis.DoesNotExist:
            return Response({'error': 'Analysis not found'}, status=404)
