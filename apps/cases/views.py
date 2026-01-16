from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Case, Evidence, AuditLog, CaseTag
from .serializers import (
    CaseSerializer,
    EvidenceSerializer,
    AuditLogSerializer,
    CaseTagSerializer,
)


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "priority", "case_type"]
    search_fields = ["name", "case_number", "description"]
    ordering_fields = ["created_at", "priority"]


# --- UI Views ---
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = "cases/case_list.html"
    context_object_name = "cases"
    ordering = ["-created_at"]


class CaseDetailView(LoginRequiredMixin, DetailView):
    model = Case
    template_name = "cases/case_detail.html"
    context_object_name = "case"


class CaseCreateView(LoginRequiredMixin, CreateView):
    model = Case
    fields = ["name", "description", "priority", "case_type"]
    template_name = "cases/case_form.html"
    success_url = reverse_lazy("ui-case-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EvidenceDetailView(LoginRequiredMixin, DetailView):
    model = Evidence
    template_name = "cases/evidence_detail.html"
    context_object_name = "evidence"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["case", "source_type"]
    search_fields = ["name", "md5_hash", "sha256_hash"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filterset_fields = ["case", "user", "action"]
