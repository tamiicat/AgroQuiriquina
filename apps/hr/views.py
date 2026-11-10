from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.permissions import SUPERVISOR
from apps.core.viewsets import SyncModelViewSet

from .models import Desempeno, Remuneracion
from .serializers import DesempenoSerializer, RemuneracionSerializer


class DesempenoViewSet(SyncModelViewSet):
    queryset = Desempeno.objects.select_related("trabajador")
    serializer_class = DesempenoSerializer
    read_roles = [SUPERVISOR]
    write_roles = [SUPERVISOR]
    filterset_fields = {"trabajador": ["exact"], "labor": ["exact"],
                        "fecha": ["exact", "gte", "lte"]}
    ordering_fields = ["fecha"]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)

    def _bloquear_si_liquidado(self, instance):
        if instance.remuneracion_id:
            raise ValidationError("Este registro ya fue incluido en una remuneración.")

    def perform_update(self, serializer):
        self._bloquear_si_liquidado(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._bloquear_si_liquidado(instance)
        super().perform_destroy(instance)


class RemuneracionViewSet(SyncModelViewSet):
    """Nómina: solo administrador."""
    queryset = Remuneracion.objects.select_related("trabajador")
    serializer_class = RemuneracionSerializer
    read_roles = []
    write_roles = []
    filterset_fields = {"trabajador": ["exact"], "estado": ["exact"],
                        "periodo_fin": ["gte", "lte"]}

    def _cambiar_estado(self, desde, hasta):
        rem = self.get_object()
        if rem.estado != desde:
            raise ValidationError(f"La remuneración debe estar en estado {desde}.")
        rem.estado = hasta
        rem.save(update_fields=["estado", "updated_at"])
        return Response(self.get_serializer(rem).data)

    @action(detail=True, methods=["post"])
    def calcular(self, request, pk=None):
        rem = self.get_object()
        if rem.estado != Remuneracion.Estado.BORRADOR:
            raise ValidationError("Solo se recalculan remuneraciones en borrador.")
        rem.calcular()
        return Response(self.get_serializer(rem).data)

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        return self._cambiar_estado(Remuneracion.Estado.BORRADOR, Remuneracion.Estado.APROBADA)

    @action(detail=True, methods=["post"])
    def pagar(self, request, pk=None):
        return self._cambiar_estado(Remuneracion.Estado.APROBADA, Remuneracion.Estado.PAGADA)
