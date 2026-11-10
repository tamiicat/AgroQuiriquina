from rest_framework.routers import SimpleRouter

from .views import DesempenoViewSet, RemuneracionViewSet

router = SimpleRouter()
router.register("desempenos", DesempenoViewSet, basename="desempeno")
router.register("remuneraciones", RemuneracionViewSet, basename="remuneracion")

urlpatterns = router.urls
