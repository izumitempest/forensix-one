from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from core.views import IndexView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # UI Routes
    path("cases/", include("apps.cases.urls_ui")),
    path("acquisition/", include("apps.acquisition.urls_ui")),
    path("analysis/", include("apps.analysis.urls_ui")),
    path("reporting/", include("apps.reporting.urls_ui")),
    path("timeline/", include("apps.timeline.urls_ui")),
    path("collaboration/", include("apps.collaboration.urls_ui")),
    # API Endpoints
    path("api/cases/", include("apps.cases.urls")),
    path("api/acquisition/", include("apps.acquisition.urls")),
    path("api/analysis/", include("apps.analysis.urls")),
    path("api/reporting/", include("apps.reporting.urls")),
    path("api/timeline/", include("apps.timeline.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
