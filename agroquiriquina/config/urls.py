from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Ping liviano para que la app móvil detecte si hay conexión con el servidor."""
    return Response({"status": "ok"})


def front(name):
    """Sirve la app web (PWA) que vive en /frontend. sw.js debe colgar de la raíz."""
    return lambda request: serve(request, name, document_root=settings.BASE_DIR / "frontend")


urlpatterns = [
    path("", front("index.html"), name="app"),
    path("sw.js", front("sw.js"), name="sw"),
    path("manifest.json", front("manifest.json"), name="manifest"),
    path("admin/", admin.site.urls),
    path("api/v1/health/", health, name="health"),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/sync/", include("apps.sync.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.inventory.urls")),
    path("api/v1/", include("apps.sales.urls")),
    path("api/v1/", include("apps.hr.urls")),
]
