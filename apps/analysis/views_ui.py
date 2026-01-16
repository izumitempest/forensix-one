from django.views import View
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.cases.models import Evidence
from .models import Analysis
from .tasks import start_evidence_analysis


class StartAnalysisView(LoginRequiredMixin, View):
    """Triggers analysis for a specific evidence item from the UI"""

    def post(self, request, pk):
        evidence = get_object_or_404(Evidence, pk=pk)

        # Create a new Analysis record
        analysis = Analysis.objects.create(evidence=evidence, type="deep_file")

        # Trigger the Celery task
        start_evidence_analysis.delay(analysis.id)

        # Redirect back to evidence detail
        return redirect("ui-evidence-detail", pk=pk)


class AnalysisListView(LoginRequiredMixin, ListView):
    """Dashbord view for all forensic analysis jobs"""

    model = Analysis
    template_name = "analysis/analysis_list.html"
    context_object_name = "analyses"
    ordering = ["-started_at"]
