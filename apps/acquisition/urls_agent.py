from django.urls import path
from .views import AgentDeployView, AgentStreamView

urlpatterns = [
    path("", AgentDeployView.as_view(), name="agent-deploy"),
    path("stream/<uuid:task_id>/", AgentStreamView.as_view(), name="agent-stream"),
]
