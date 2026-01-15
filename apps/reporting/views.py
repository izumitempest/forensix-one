from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Report, ReportTemplate
from .serializers import ReportSerializer, ReportTemplateSerializer
from .generator import ReportGenerator

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    filterset_fields = ['case', 'format']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Triggers the report generation process"""
        report = self.get_object()
        generator = ReportGenerator(report)
        
        if report.format == 'pdf':
            file_path = generator.generate_pdf()
        elif report.format == 'case':
            case_json = generator.export_as_case()
            return Response({'case_json': case_json})
        else:
            return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)
            
        if file_path:
            return Response({'status': 'generated', 'file_path': file_path})
        return Response({'status': 'failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReportTemplateViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
