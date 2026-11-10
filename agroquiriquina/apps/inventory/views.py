from decimal import Decimal, InvalidOperation

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import HasRole, SUPERVISOR, VENDEDOR
from apps.core.viewsets import SyncModelViewSet

from .models import InsumoAgricola, MovimientoStock, ProductoVenta
from .serializers import (InsumoAgricolaSerializer, MovimientoInputSerializer,
                          MovimientoStockSerializer, ProductoVentaSerializer)
from .services import StockInsuficiente, aplicar_movimiento


class MovimientoActionMixin:
    @action(detail=True, methods=["post"])
    def movimiento(self, request, pk=None):
        """Registra entrada/salida/ajuste de stock (solo administrador)."""
        item = self.get_object()
        ser = MovimientoInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            mov, faltante = aplicar_movimiento(item.pk, usuario=request.user, **ser.validated_data)
        except StockInsuficiente as exc:
            raise ValidationError({"cantidad": str(exc)})
        item.refresh_from_db()
        return Response({
            "movimiento": MovimientoStockSerializer(mov).data,
            "cantidad_disponible": item.cantidad_disponible,
        })


class ProductoVentaViewSet(MovimientoActionMixin, SyncModelViewSet):
    queryset = ProductoVenta.objects.all()
    serializer_class = ProductoVentaSerializer
    read_roles = [VENDEDOR, SUPERVISOR]
    write_roles = []
    search_fields = ["nombre", "variedad"]
    filterset_fields = ["categoria", "activo"]


class InsumoAgricolaViewSet(MovimientoActionMixin, SyncModelViewSet):
    queryset = InsumoAgricola.objects.all()
    serializer_class = InsumoAgricolaSerializer
    read_roles = [SUPERVISOR]
    write_roles = []
    search_fields = ["nombre"]
    filterset_fields = ["tipo", "activo"]

    @action(detail=True, methods=["get"])
    def requerimiento(self, request, pk=None):
        """GET /insumos/<id>/requerimiento/?hectareas=12.5 -> insumo necesario y si alcanza."""
        insumo = self.get_object()
        try:
            hectareas = Decimal(request.query_params.get("hectareas", ""))
            if hectareas <= 0:
                raise InvalidOperation
        except InvalidOperation:
            raise ValidationError({"hectareas": "Indica un número mayor que 0."})
        requerido = insumo.calcular_requerimiento(hectareas)
        return Response({
            "insumo": insumo.nombre,
            "hectareas": hectareas,
            "unidad_medida": insumo.unidad_medida,
            "requerido": requerido,
            "disponible": insumo.cantidad_disponible,
            "faltante": max(requerido - insumo.cantidad_disponible, Decimal("0")),
            "alcanza": insumo.cantidad_disponible >= requerido,
        })


class MovimientoStockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoStock.objects.select_related("item", "usuario")
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated, HasRole]
    read_roles = [SUPERVISOR]
    filterset_fields = {"item": ["exact"], "tipo": ["exact"], "created_at": ["gte", "lte"]}
