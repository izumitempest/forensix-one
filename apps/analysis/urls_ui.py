from django.urls import path
from .views_ui import StartAnalysisView, AnalysisListView

urlpatterns = [
    path("", AnalysisListView.as_view(), name="ui-analysis-list"),
    path("start/<uuid:pk>/", StartAnalysisView.as_view(), name="ui-analysis-start"),
]
