from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .permissions import HasRole
from .utils import parse_updated_since


class SyncQuerysetMixin:
    """
    - Sin parámetros: devuelve solo registros no borrados.
    - Con ?updated_since=<ISO8601>: devuelve todo lo modificado desde esa fecha,
      INCLUYENDO borrados lógicos (is_deleted=true) para que el móvil los elimine.
    """
    permission_classes = [IsAuthenticated, HasRole]

    def get_queryset(self):
        qs = super().get_queryset()
        since = parse_updated_since(self.request)
        if since:
            return qs.filter(updated_at__gt=since)
        return qs.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])


class SyncModelViewSet(SyncQuerysetMixin, viewsets.ModelViewSet):
    pass
