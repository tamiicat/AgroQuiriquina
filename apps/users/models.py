from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import SyncModel
from apps.core.validators import normalizar_rut, validar_rut


class Rol(models.TextChoices):
    ADMINISTRADOR = "ADMIN", "Administrador"
    VENDEDOR = "VENDEDOR", "Vendedor"
    SUPERVISOR_TERRENO = "SUPERVISOR", "Supervisor de Terreno"


class User(AbstractUser):
    """Usuario del sistema (login). RBAC mediante `rol`."""
    rol = models.CharField(max_length=15, choices=Rol.choices, default=Rol.VENDEDOR)
    persona = models.OneToOneField(
        "users.Persona", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="usuario",
    )

    @property
    def es_admin(self):
        return self.rol == Rol.ADMINISTRADOR


# ---------------------------------------------------------------------------
# Superclase Persona (Multi-table inheritance)
# ---------------------------------------------------------------------------
class Persona(SyncModel):
    rut = models.CharField("RUT/DNI", max_length=12, unique=True, validators=[validar_rut])
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=80, blank=True)
    region = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["nombre"]
        indexes = [models.Index(fields=["nombre"])]

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


class Cliente(Persona):
    class Tipo(models.TextChoices):
        MAYORISTA = "MAYORISTA", "Mayorista"
        MINORISTA = "MINORISTA", "Minorista"
        FERIA = "FERIA", "Feria / Locatario"

    tipo = models.CharField(max_length=12, choices=Tipo.choices, default=Tipo.MINORISTA)
    razon_social = models.CharField(max_length=150, blank=True)
    limite_credito = models.DecimalField(max_digits=14, decimal_places=0, default=0)


class Proveedor(Persona):
    rubro = models.CharField(max_length=100, blank=True)  # semillas, fertilizantes, transporte...
    condiciones_pago = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name_plural = "proveedores"


class Trabajador(Persona):
    class TipoContrato(models.TextChoices):
        TEMPORERO = "TEMPORERO", "Temporero"
        PLAZO_FIJO = "PLAZO_FIJO", "Plazo fijo"
        INDEFINIDO = "INDEFINIDO", "Indefinido"

    tipo_contrato = models.CharField(max_length=12, choices=TipoContrato.choices,
                                     default=TipoContrato.TEMPORERO)
    cargo = models.CharField(max_length=80, blank=True)
    tarifa_diaria = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    fecha_ingreso = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "trabajadores"
