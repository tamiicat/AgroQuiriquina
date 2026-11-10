from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (ClienteViewSet, MeView, ProveedorViewSet,
                    TrabajadorViewSet, UserViewSet)

router = SimpleRouter()
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("proveedores", ProveedorViewSet, basename="proveedor")
router.register("trabajadores", TrabajadorViewSet, basename="trabajador")
router.register("usuarios", UserViewSet, basename="usuario")

urlpatterns = [path("me/", MeView.as_view(), name="me")] + router.urls
