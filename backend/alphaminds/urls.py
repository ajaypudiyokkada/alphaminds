from django.contrib import admin
from django.conf import settings
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def favicon(request):
    """Browsers ask for /favicon.ico on pages without <link rel=icon> (admin, API docs)."""
    return redirect(static("landing/branding/favicon.ico"), permanent=True)


urlpatterns = [
    path("favicon.ico", favicon),
    path("admin/", admin.site.urls),
    path("", include("frontend.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/v1/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]
