from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaseViewSet, EvidenceViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'cases', CaseViewSet)
router.register(r'evidence', EvidenceViewSet)
router.register(r'audit', AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
