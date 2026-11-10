from decimal import Decimal

from django.db import models, transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum

from apps.core.models import SyncModel


class Remuneracion(SyncModel):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        APROBADA = "APROBADA", "Aprobada"
        PAGADA = "PAGADA", "Pagada"

    trabajador = models.ForeignKey("users.Trabajador", on_delete=models.PROTECT, related_name="remuneraciones")
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    total_produccion = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    bonos = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    descuentos = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_liquido = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)

    class Meta:
        ordering = ["-periodo_fin"]
        verbose_name_plural = "remuneraciones"
        constraints = [
            models.CheckConstraint(check=Q(periodo_fin__gte=F("periodo_inicio")),
                                   name="remuneracion_periodo_valido"),
        ]

    @transaction.atomic
    def calcular(self):
        """Suma los desempeños del periodo aún no liquidados y calcula el líquido."""
        pendientes = Desempeno.objects.filter(
            trabajador=self.trabajador,
            fecha__range=(self.periodo_inicio, self.periodo_fin),
            is_deleted=False,
        ).filter(Q(remuneracion__isnull=True) | Q(remuneracion=self))

        monto = ExpressionWrapper(F("cantidad") * F("tarifa_unitaria"),
                                  output_field=DecimalField(max_digits=16, decimal_places=2))
        total = pendientes.aggregate(t=Sum(monto))["t"] or Decimal("0")

        self.total_produccion = total.quantize(Decimal("1"))
        self.total_liquido = self.total_produccion + self.bonos - self.descuentos
        self.save()
        pendientes.update(remuneracion=self)   # evita pagar dos veces el mismo registro
        return self.total_liquido

    def __str__(self):
        return f"{self.trabajador.nombre} {self.periodo_inicio}→{self.periodo_fin}: ${self.total_liquido}"


class Desempeno(SyncModel):
    """Producción diaria registrada en terreno (offline-friendly)."""
    class Labor(models.TextChoices):
        COSECHA_PAPA = "COSECHA_PAPA", "Cosecha de papa"
        ENSACADO = "ENSACADO", "Ensacado"
        SIEMBRA = "SIEMBRA", "Siembra"
        CARGA = "CARGA", "Carga / Estiba"
        JORNAL = "JORNAL", "Jornal diario"
        OTRA = "OTRA", "Otra"

    class UnidadProduccion(models.TextChoices):
        SACO = "SACO", "Sacos"
        KILO = "KG", "Kilos"
        JORNADA = "JORNADA", "Jornadas"

    trabajador = models.ForeignKey("users.Trabajador", on_delete=models.PROTECT, related_name="desempenos")
    registrado_por = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="desempenos_registrados")
    fecha = models.DateField()
    labor = models.CharField(max_length=15, choices=Labor.choices)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    unidad = models.CharField(max_length=8, choices=UnidadProduccion.choices, default=UnidadProduccion.SACO)
    tarifa_unitaria = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Tarifa vigente al momento del registro (snapshot).",
    )
    remuneracion = models.ForeignKey(Remuneracion, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="desempenos")
    device_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name_plural = "desempeños"
        indexes = [models.Index(fields=["trabajador", "fecha"])]

    @property
    def monto(self) -> Decimal:
        return (self.cantidad * self.tarifa_unitaria).quantize(Decimal("1"))
