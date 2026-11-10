from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (CuentasPorCobrarView, DespachoViewSet, PagoViewSet,
                    RentabilidadView, VentaViewSet)

router = SimpleRouter()
router.register("ventas", VentaViewSet, basename="venta")
router.register("pagos", PagoViewSet, basename="pago")
router.register("despachos", DespachoViewSet, basename="despacho")

urlpatterns = [
    path("finanzas/cuentas-por-cobrar/", CuentasPorCobrarView.as_view(), name="cuentas-por-cobrar"),
    path("finanzas/rentabilidad/", RentabilidadView.as_view(), name="rentabilidad"),
] + router.urls
