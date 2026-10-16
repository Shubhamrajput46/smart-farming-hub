from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve as serve_media

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def healthz(request):
    """Render/uptime monitors ke liye: app + database chal raha hai ya nahi."""
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "db-error"}, status=503)
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('healthz/', healthz, name='healthz'),
    # Uploaded files: sirf logged-in users (FarmerMiddleware login maangta hai)
    re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
    path('admin/', admin.site.urls),
    
    path('notifications/', include('notifications.urls')),
    path('api/', include('api.urls')), 
    path('accounts/', include('accounts.urls')),
    path('', include('farms.urls')),
    path('finance/', include('finance.urls')),
    path('services/', include('ai_services.urls')),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

]

