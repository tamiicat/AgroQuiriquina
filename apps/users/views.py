from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasRole, SUPERVISOR, VENDEDOR
from apps.core.viewsets import SyncModelViewSet

from .models import Cliente, Proveedor, Trabajador, User
from .serializers import (ClienteSerializer, ProveedorSerializer,
                          TrabajadorSerializer, UserSerializer)


class ClienteViewSet(SyncModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    read_roles = [VENDEDOR]
    write_roles = [VENDEDOR]
    search_fields = ["nombre", "rut", "razon_social"]
    filterset_fields = ["tipo", "comuna"]


class ProveedorViewSet(SyncModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    read_roles = [VENDEDOR]
    write_roles = []          # solo administrador
    search_fields = ["nombre", "rut", "rubro"]


class TrabajadorViewSet(SyncModelViewSet):
    queryset = Trabajador.objects.all()
    serializer_class = TrabajadorSerializer
    read_roles = [SUPERVISOR]
    write_roles = [SUPERVISOR]
    search_fields = ["nombre", "rut"]
    filterset_fields = ["tipo_contrato", "activo"]


class UserViewSet(viewsets.ModelViewSet):
    """Gestión de usuarios del sistema: solo administrador."""
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, HasRole]
    read_roles = []
    write_roles = []


class MeView(APIView):
    """Datos del usuario autenticado (la app lo usa para decidir qué pantallas mostrar)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "nombre": u.get_full_name() or u.username,
            "rol": u.rol,
            "persona": str(u.persona_id) if u.persona_id else None,
        })
