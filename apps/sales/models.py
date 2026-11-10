from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from apps.core.models import SyncModel


class Venta(SyncModel):
    class Estado(models.TextChoices):
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        ANULADA = "ANULADA", "Anulada"

    cliente = models.ForeignKey("users.Cliente", on_delete=models.PROTECT, related_name="ventas")
    vendedor = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="ventas")
    fecha = models.DateTimeField()  # momento real de la venta (puede ser offline)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.CONFIRMADA)
    total = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    observaciones = models.TextField(blank=True)

    # Metadatos de sincronización offline
    device_id = models.CharField(max_length=64, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    requiere_revision = models.BooleanField(
        default=False, help_text="Ej: stock insuficiente al sincronizar una venta offline."
    )

    class Meta:
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["cliente", "-fecha"])]

    def recalcular_total(self, save=True):
        self.total = self.detalles.aggregate(t=Sum("subtotal"))["t"] or Decimal("0")
        if save:
            self.save(update_fields=["total", "updated_at"])
        return self.total

    @property
    def total_pagado(self) -> Decimal:
        return self.pagos.filter(estado=Pago.Estado.PAGADO).aggregate(t=Sum("monto"))["t"] or Decimal("0")

    @property
    def saldo_pendiente(self) -> Decimal:
        return self.total - self.total_pagado

    @property
    def estado_pago(self) -> str:
        pagado = self.total_pagado
        if self.total > 0 and pagado >= self.total:
            return Pago.Estado.PAGADO
        return Pago.Estado.PARCIAL if pagado > 0 else Pago.Estado.PENDIENTE

    def __str__(self):
        return f"Venta {str(self.id)[:8]} - {self.cliente.nombre} - ${self.total}"


class DetalleVenta(SyncModel):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("inventory.ProductoVenta", on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=0, editable=False, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal("1"))
        super().save(*args, **kwargs)


class Pago(SyncModel):
    """Abono o cuota. Las cuentas por cobrar se derivan de aquí."""
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PARCIAL = "PARCIAL", "Parcial"     # solo como estado derivado de la Venta
        PAGADO = "PAGADO", "Pagado"
        ANULADO = "ANULADO", "Anulado"

    class Metodo(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        CHEQUE = "CHEQUE", "Cheque"
        CREDITO = "CREDITO", "Crédito (por cobrar)"

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="pagos")
    monto = models.DecimalField(max_digits=14, decimal_places=0)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    metodo = models.CharField(max_length=15, choices=Metodo.choices, default=Metodo.EFECTIVO)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.estado == self.Estado.PAGADO and not self.fecha_pago:
            self.fecha_pago = timezone.now()
        super().save(*args, **kwargs)


class Despacho(SyncModel):
    class Estado(models.TextChoices):
        PROGRAMADO = "PROGRAMADO", "Programado"
        EN_RUTA = "EN_RUTA", "En ruta"
        ENTREGADO = "ENTREGADO", "Entregado"
        CANCELADO = "CANCELADO", "Cancelado"

    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name="despacho")
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    direccion = models.CharField(max_length=255)
    comuna = models.CharField(max_length=80, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PROGRAMADO)
    transportista = models.CharField(max_length=100, blank=True)
    patente = models.CharField(max_length=10, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["fecha", "hora"]
        verbose_name_plural = "despachos"
