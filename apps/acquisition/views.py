from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AcquisitionTask
from .serializers import AcquisitionTaskSerializer

class AcquisitionTaskViewSet(viewsets.ModelViewSet):
    queryset = AcquisitionTask.objects.all()
    serializer_class = AcquisitionTaskSerializer
    filterset_fields = ['status', 'type']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Triggers the background acquisition task"""
        task = self.get_object()
        from .tasks import run_acquisition
        run_acquisition.delay(task.id)
        
        task.status = 'queued'
        task.save()
        return Response({'status': 'acquisition queued', 'task_id': task.id})
