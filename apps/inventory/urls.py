from rest_framework.routers import SimpleRouter

from .views import InsumoAgricolaViewSet, MovimientoStockViewSet, ProductoVentaViewSet

router = SimpleRouter()
router.register("productos", ProductoVentaViewSet, basename="producto")
router.register("insumos", InsumoAgricolaViewSet, basename="insumo")
router.register("movimientos", MovimientoStockViewSet, basename="movimiento")

urlpatterns = router.urls
