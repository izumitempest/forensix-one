from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Case, Evidence, AuditLog, CaseTag
from .serializers import CaseSerializer, EvidenceSerializer, AuditLogSerializer, CaseTagSerializer

class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'case_type']
    search_fields = ['name', 'case_number', 'description']
    ordering_fields = ['created_at', 'priority']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['case', 'source_type']
    search_fields = ['name', 'md5_hash', 'sha256_hash']

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filterset_fields = ['case', 'user', 'action']
