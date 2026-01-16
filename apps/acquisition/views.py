from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AcquisitionTask
from .serializers import AcquisitionTaskSerializer


class AcquisitionTaskViewSet(viewsets.ModelViewSet):
    queryset = AcquisitionTask.objects.all()
    serializer_class = AcquisitionTaskSerializer
    filterset_fields = ["status", "type"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Triggers the background acquisition task"""
        task = self.get_object()
        from .tasks import run_acquisition

        if task.type in ["disk_physical", "disk_expert"]:
            run_acquisition.apply_async(args=[task.id], queue="privileged")
        else:
            run_acquisition.delay(task.id)

        task.status = "queued"
        task.save()
        return Response({"status": "acquisition queued", "task_id": task.id})


# --- UI Views ---
import os
import logging
from django.views.generic import ListView, CreateView, View
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import AcquisitionForm

logger = logging.getLogger(__name__)


class AcquisitionListView(LoginRequiredMixin, ListView):
    model = AcquisitionTask
    template_name = "acquisition/task_list.html"
    context_object_name = "tasks"
    ordering = ["-created_at"]


class AcquisitionCreateView(LoginRequiredMixin, CreateView):
    model = AcquisitionTask
    form_class = AcquisitionForm
    template_name = "acquisition/task_form.html"
    success_url = reverse_lazy("ui-acquisition-list")

    def get_initial(self):
        initial = super().get_initial()
        case_id = self.request.GET.get("case_id")
        if case_id:
            from apps.cases.models import Case

            initial["case"] = get_object_or_404(Case, pk=case_id)
        return initial

    def form_valid(self, form):
        form.save(user=self.request.user)
        return redirect(self.success_url)


class StartAcquisitionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(AcquisitionTask, pk=pk)
        from .tasks import run_acquisition

        if task.type in ["disk_physical", "disk_expert"]:
            run_acquisition.apply_async(args=[task.id], queue="privileged")
        else:
            run_acquisition.delay(task.id)
        task.status = "queued"
        task.save()
        messages.success(request, f"Acquisition started for {task.evidence.name}")
        return redirect("ui-acquisition-list")


class AgentDeployView(View):
    """
    Serves the bootstrap shell script for the Remote Forensic Agent.
    Usage: curl -sSL http://<host>/agent | bash -s -- --key <connection_key>
    """

    def get(self, request):
        from django.http import HttpResponse

        # This is a mock/minimal agent for the pillar implementation.
        # In production, this would be a compiled binary or a more robust Python script.
        script = """#!/bin/bash
echo "--- ForensixOne Remote Agent Deployment ---"
KEY=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --key) KEY="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$KEY" ]; then
    echo "ERROR: Connection key is required."
    exit 1
fi

echo "[AGENT] Connection established using key: $KEY"
echo "[AGENT] Collecting system telemetry..."

(
  echo "=== FORENSIX ONE REMOTE TELEMETRY REPORT ==="
  echo "Timestamp: $(date -u)"
  echo ""
  echo "--- SYSTEM IDENTIFICATION ---"
  uname -a
  echo ""
  echo "--- NETWORK STATE (ACTIVE CONNECTIONS) ---"
  netstat -ant 2>/dev/null || ss -ant
  echo ""
  echo "--- RUNNING PROCESSES ---"
  ps auxww
  echo ""
  echo "--- MOUNTED DISKS & BLK DEVICES ---"
  lsblk
  echo ""
  echo "--- USER SESSIONS ---"
  who
  echo "=== END OF REPORT ==="
) > /tmp/report.txt

# Upload with Content-Length to avoid chunked encoding issues with dev server
curl -i -sS -H "Content-Type: application/octet-stream" -T /tmp/report.txt "http://{{ host }}/agent/stream/$KEY"
rm /tmp/report.txt

echo "[AGENT] Transmission complete. Agent self-destructing..."
"""
        # Inject host for feedback
        script = script.replace("{{ host }}", request.get_host())

        return HttpResponse(script, content_type="text/x-shellscript")


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name="dispatch")
class AgentStreamView(View):
    """
    Receives real-time forensic data from the deployed agent.
    Endpoint: /agent/stream/<uuid:task_id>/
    """

    def put(self, request, task_id):
        """Map PUT to POST logic for curl -T compatibility"""
        return self.post(request, task_id)

    def post(self, request, task_id):
        task = get_object_or_404(AcquisitionTask, pk=task_id)

        # Ensure the destination path exists
        dest_dir = os.path.dirname(task.destination_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        logger.info(f"Receiving forensic stream for Task {task_id}")

        try:
            with open(task.destination_path, "wb") as f:
                # Read chunks directly from the request stream
                while True:
                    chunk = request.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)

                    # Optional: Update progress based on bytes received
                    # Since we don't know total size, we just show 'Receiving...' in speed
                    task.current_speed = "Receiving Data..."
                    task.save()

            # Finalize task status for the orchestrator to see
            task.progress_percent = 100
            task.status = "completed"
            task.completed_at = timezone.now()
            task.current_speed = "Stream Complete"
            task.save()

            return HttpResponse("Stream received successfully", status=200)

        except Exception as e:
            logger.error(f"Stream ingestion failed for {task_id}: {e}")
            task.status = "failed"
            task.error_message = f"Stream Error: {str(e)}"
            task.save()
            return HttpResponse(f"Error: {str(e)}", status=500)
