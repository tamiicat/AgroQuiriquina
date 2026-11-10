from collections import defaultdict
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ADMIN, HasRole, VENDEDOR
from apps.core.viewsets import SyncModelViewSet, SyncQuerysetMixin
from apps.hr.models import Remuneracion

from .models import DetalleVenta, Despacho, Pago, Venta
from .serializers import (DespachoSerializer, PagoSerializer, VentaSerializer)
from .services import anular_venta


def _solo_propias(qs, user, campo):
    """Un vendedor solo ve lo suyo; el administrador ve todo."""
    if user.rol == VENDEDOR and not user.is_superuser:
        return qs.filter(**{campo: user})
    return qs


class VentaViewSet(SyncQuerysetMixin, mixins.CreateModelMixin, mixins.ListModelMixin,
                   mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Crear / listar / ver ventas. No se editan: se anulan (acción `anular`)."""
    queryset = (Venta.objects.select_related("cliente", "despacho")
                .prefetch_related("detalles", "pagos"))
    serializer_class = VentaSerializer
    read_roles = [VENDEDOR]
    write_roles = [VENDEDOR]
    search_fields = ["cliente__nombre", "cliente__rut"]
    filterset_fields = {"cliente": ["exact"], "estado": ["exact"],
                        "fecha": ["gte", "lte"], "requiere_revision": ["exact"]}
    ordering_fields = ["fecha", "total"]

    def get_queryset(self):
        return _solo_propias(super().get_queryset(), self.request.user, "vendedor")

    def perform_create(self, serializer):
        serializer.save(vendedor=self.request.user, synced_at=timezone.now())

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        venta = anular_venta(self.get_object(), request.user)
        return Response(self.get_serializer(venta).data)


class PagoViewSet(SyncModelViewSet):
    queryset = Pago.objects.select_related("venta")
    serializer_class = PagoSerializer
    read_roles = [VENDEDOR]
    write_roles = [VENDEDOR]
    filterset_fields = {"venta": ["exact"], "estado": ["exact"],
                        "fecha_vencimiento": ["gte", "lte"]}

    def get_queryset(self):
        return _solo_propias(super().get_queryset(), self.request.user, "venta__vendedor")


class DespachoViewSet(SyncModelViewSet):
    queryset = Despacho.objects.select_related("venta", "venta__cliente")
    serializer_class = DespachoSerializer
    read_roles = [VENDEDOR]
    write_roles = [VENDEDOR]
    filterset_fields = {"estado": ["exact"], "fecha": ["exact", "gte", "lte"]}

    def get_queryset(self):
        return _solo_propias(super().get_queryset(), self.request.user, "venta__vendedor")


# ---------------------------------------------------------------------------
# Finanzas (solo administrador: read_roles / write_roles vacíos)
# ---------------------------------------------------------------------------
class _FinanzasView(APIView):
    permission_classes = [IsAuthenticated, HasRole]
    read_roles = []
    write_roles = []


class CuentasPorCobrarView(_FinanzasView):
    """GET /finanzas/cuentas-por-cobrar/[?cliente=<uuid>] -> deuda agrupada por cliente."""

    def get(self, request):
        dinero = DecimalField(max_digits=16, decimal_places=0)
        pagado = Coalesce(
            Sum("pagos__monto", filter=Q(pagos__estado=Pago.Estado.PAGADO)),
            Value(0), output_field=dinero,
        )
        qs = (Venta.objects
              .filter(estado=Venta.Estado.CONFIRMADA, is_deleted=False)
              .annotate(pagado=pagado)
              .annotate(saldo=ExpressionWrapper(F("total") - F("pagado"), output_field=dinero))
              .filter(saldo__gt=0)
              .select_related("cliente"))
        cliente = request.query_params.get("cliente")
        if cliente:
            qs = qs.filter(cliente_id=cliente)

        por_cliente = defaultdict(lambda: {"deuda": Decimal("0"), "ventas": 0})
        for v in qs:
            fila = por_cliente[v.cliente_id]
            fila.update(cliente=str(v.cliente_id), nombre=v.cliente.nombre, rut=v.cliente.rut)
            fila["deuda"] += v.saldo
            fila["ventas"] += 1
        filas = sorted(por_cliente.values(), key=lambda f: f["deuda"], reverse=True)
        return Response({
            "total_por_cobrar": sum((f["deuda"] for f in filas), Decimal("0")),
            "clientes": filas,
        })


class RentabilidadView(_FinanzasView):
    """GET /finanzas/rentabilidad/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD (por defecto: mes actual)."""

    def get(self, request):
        hoy = timezone.localdate()
        desde = parse_date(request.query_params.get("desde", "")) or hoy.replace(day=1)
        hasta = parse_date(request.query_params.get("hasta", "")) or hoy
        if hasta < desde:
            raise ValidationError({"hasta": "Debe ser posterior a 'desde'."})

        ventas = Venta.objects.filter(
            estado=Venta.Estado.CONFIRMADA, is_deleted=False,
            fecha__date__gte=desde, fecha__date__lte=hasta)
        total_ventas = ventas.aggregate(t=Sum("total"))["t"] or Decimal("0")
        cobrado = (Pago.objects.filter(venta__in=ventas, estado=Pago.Estado.PAGADO)
                   .aggregate(t=Sum("monto"))["t"] or Decimal("0"))
        nomina = (Remuneracion.objects
                  .filter(estado__in=[Remuneracion.Estado.APROBADA, Remuneracion.Estado.PAGADA],
                          periodo_fin__gte=desde, periodo_fin__lte=hasta, is_deleted=False)
                  .aggregate(t=Sum("total_liquido"))["t"] or Decimal("0"))
        por_categoria = list(
            DetalleVenta.objects.filter(venta__in=ventas)
            .values("producto__categoria").annotate(total=Sum("subtotal")).order_by("-total"))

        return Response({
            "desde": desde, "hasta": hasta,
            "ventas_totales": total_ventas,
            "cobrado": cobrado,
            "por_cobrar": total_ventas - cobrado,
            "costo_nomina": nomina,
            "margen_estimado": total_ventas - nomina,
            "ventas_por_categoria": [
                {"categoria": r["producto__categoria"], "total": r["total"]} for r in por_categoria],
            "nota": "Margen estimado = ventas - nómina aprobada/pagada. "
                    "Aún no incluye costo de insumos ni compras a proveedores.",
        })
