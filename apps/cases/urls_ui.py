from django.urls import path
from .views import CaseListView, CaseDetailView, CaseCreateView, EvidenceDetailView

urlpatterns = [
    path("", CaseListView.as_view(), name="ui-case-list"),
    path("new/", CaseCreateView.as_view(), name="ui-case-create"),
    path("<uuid:pk>/", CaseDetailView.as_view(), name="ui-case-detail"),
    path(
        "evidence/<uuid:pk>/", EvidenceDetailView.as_view(), name="ui-evidence-detail"
    ),
]
