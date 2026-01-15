from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalysisViewSet, ArtifactViewSet

router = DefaultRouter()
router.register(r'analyses', AnalysisViewSet)
router.register(r'artifacts', ArtifactViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
