from django.urls import path
from .views import AcquisitionListView, AcquisitionCreateView, StartAcquisitionView

urlpatterns = [
    path("", AcquisitionListView.as_view(), name="ui-acquisition-list"),
    path("new/", AcquisitionCreateView.as_view(), name="ui-acquisition-create"),
    path(
        "start/<uuid:pk>/", StartAcquisitionView.as_view(), name="ui-acquisition-start"
    ),
]
