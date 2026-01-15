from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Analysis, Artifact
from .serializers import AnalysisSerializer, ArtifactSerializer
from .tasks import start_evidence_analysis
from .ai_service import AICopilotService

class AnalysisViewSet(viewsets.ModelViewSet):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Triggers the background analysis task"""
        analysis = self.get_object()
        start_evidence_analysis.delay(analysis.id)
        return Response({'status': 'analysis started'})

    @action(detail=True, methods=['post'])
    def ask_ai(self, request, pk=None):
        """UVP: Ask the Built-in AI copilot about this analysis"""
        analysis = self.get_object()
        question = request.data.get('question')
        if not question:
            return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        artifacts = analysis.artifacts.all()
        ai_service = AICopilotService()
        answer = ai_service.answer_question(question, artifacts)
        
        return Response({'answer': answer})

class ArtifactViewSet(viewsets.ModelViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    filterset_fields = ['analysis', 'type', 'is_suspicious']
