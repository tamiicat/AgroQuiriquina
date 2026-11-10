from django.db import transaction
from django.utils import timezone

from apps.inventory.models import MovimientoStock
from apps.inventory.services import aplicar_movimiento

from .models import DetalleVenta, Despacho, Pago, Venta


@transaction.atomic
def registrar_venta(validated_data):
    """
    Crea la venta con sus detalles, pagos y despacho, y descuenta el stock.
    Si el stock no alcanza NO se rechaza (la venta ya ocurrió en terreno):
    se descuenta lo disponible y se marca `requiere_revision=True`.
    """
    detalles = validated_data.pop("detalles")
    pagos = validated_data.pop("pagos", [])
    despacho = validated_data.pop("despacho", None)

    venta = Venta.objects.create(**validated_data)
    for d in detalles:
        DetalleVenta.objects.create(venta=venta, **d)
    for p in pagos:
        Pago.objects.create(venta=venta, **p)
    if despacho:
        Despacho.objects.create(venta=venta, **despacho)

    venta.recalcular_total(save=False)

    for d in venta.detalles.select_related("producto"):
        _, faltante = aplicar_movimiento(
            d.producto_id, MovimientoStock.Tipo.SALIDA, d.cantidad,
            usuario=venta.vendedor, motivo=f"Venta {str(venta.id)[:8]}",
            referencia=venta.id, permitir_faltante=True,
        )
        if faltante > 0:
            venta.requiere_revision = True

    venta.save(update_fields=["total", "requiere_revision", "updated_at"])
    return venta


@transaction.atomic
def anular_venta(venta, usuario):
    """Anula la venta, repone el stock y anula pagos pendientes."""
    if venta.estado == Venta.Estado.ANULADA:
        return venta
    for d in venta.detalles.all():
        aplicar_movimiento(
            d.producto_id, MovimientoStock.Tipo.ENTRADA, d.cantidad,
            usuario=usuario, motivo=f"Anulación venta {str(venta.id)[:8]}", referencia=venta.id,
        )
    venta.pagos.filter(estado=Pago.Estado.PENDIENTE).update(
        estado=Pago.Estado.ANULADO, updated_at=timezone.now())
    venta.estado = Venta.Estado.ANULADA
    venta.save(update_fields=["estado", "updated_at"])
    return venta
