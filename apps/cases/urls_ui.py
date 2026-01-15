from django.urls import path
from .views import CaseListView, CaseDetailView, CaseCreateView

urlpatterns = [
    path("", CaseListView.as_view(), name="case-list"),
    path("new/", CaseCreateView.as_view(), name="case-create"),
    path("<uuid:pk>/", CaseDetailView.as_view(), name="case-detail"),
]
