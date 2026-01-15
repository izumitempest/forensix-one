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

        run_acquisition.delay(task.id)

        task.status = "queued"
        task.save()
        return Response({"status": "acquisition queued", "task_id": task.id})


# --- UI Views ---
from django.views.generic import ListView, CreateView, View
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import AcquisitionForm


class AcquisitionListView(ListView):
    model = AcquisitionTask
    template_name = "acquisition/task_list.html"
    context_object_name = "tasks"
    ordering = ["-created_at"]


class AcquisitionCreateView(CreateView):
    model = AcquisitionTask
    form_class = AcquisitionForm
    template_name = "acquisition/task_form.html"
    success_url = reverse_lazy("acquisition-list")

    def form_valid(self, form):
        form.save(user=self.request.user)
        return redirect(self.success_url)


class StartAcquisitionView(View):
    def post(self, request, pk):
        task = get_object_or_404(AcquisitionTask, pk=pk)
        from .tasks import run_acquisition

        run_acquisition.delay(task.id)
        task.status = "queued"
        task.save()
        messages.success(request, f"Acquisition started for {task.evidence.name}")
        return redirect("acquisition-list")
