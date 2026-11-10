from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import InsumoAgricola, ProductoVenta
from apps.users.models import Cliente, Proveedor, Rol, Trabajador, User

DEFAULT_PASSWORD = "Cambiar123!"


def _dv(cuerpo: int) -> str:
    """Dígito verificador de un RUT chileno (módulo 11)."""
    suma, mult = 0, 2
    for d in reversed(str(cuerpo)):
        suma += int(d) * mult
        mult = 2 if mult == 7 else mult + 1
    resto = 11 - (suma % 11)
    return "0" if resto == 11 else "K" if resto == 10 else str(resto)


def rut(cuerpo: int) -> str:
    return f"{cuerpo}-{_dv(cuerpo)}"


# username, rol, nombre, apellido, descripción, es_superusuario, activo, RUT-cuerpo (si es trabajador)
USUARIOS_DEMO = [
    ("admin",       Rol.ADMINISTRADOR,    "Administrador", "Sistema",  "Superusuario: todo + panel /admin/", True,  True, None),
    ("gerente",     Rol.ADMINISTRADOR,    "Rodrigo",       "Fuentes",  "Rol ADMIN sin ser superusuario",     False, True, None),
    ("vendedor1",   Rol.VENDEDOR,         "María",         "González", "Vendedora (solo ve sus ventas)",     False, True, None),
    ("vendedor2",   Rol.VENDEDOR,         "Pedro",         "Soto",     "Vendedor (para probar aislamiento)", False, True, None),
    ("supervisor1", Rol.SUPERVISOR_TERRENO, "Carlos",      "Muñoz",    "Jefe de cuadrilla (terreno)",        False, True, 12345678),
    ("supervisor2", Rol.SUPERVISOR_TERRENO, "Ana",         "Rojas",    "Supervisora de bodega/terreno",      False, True, 13456789),
    ("inactivo",    Rol.VENDEDOR,         "Usuario",       "Bloqueado", "Cuenta desactivada: el login debe fallar", False, False, None),
]


class Command(BaseCommand):
    help = "Crea usuarios de prueba (uno o más por rol) y datos de ejemplo para probar la API."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=DEFAULT_PASSWORD,
                            help=f"Clave para los usuarios demo (por defecto {DEFAULT_PASSWORD}).")
        parser.add_argument("--reset", action="store_true",
                            help="Restablece clave, rol y estado de los usuarios demo que ya existen.")

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        reset = options["reset"]

        for username, rol, nombre, apellido, _desc, es_super, activo, rut_cuerpo in USUARIOS_DEMO:
            persona = None
            if rut_cuerpo:  # supervisores de terreno: también existen como Trabajador
                persona, _ = Trabajador.objects.get_or_create(rut=rut(rut_cuerpo), defaults={
                    "nombre": f"{nombre} {apellido}", "tipo_contrato": "INDEFINIDO",
                    "cargo": "Supervisor de terreno", "tarifa_diaria": 35000})

            defaults = {"rol": rol, "first_name": nombre, "last_name": apellido,
                        "email": f"{username}@agroquiriquina.local", "is_active": activo,
                        "is_staff": es_super, "is_superuser": es_super, "persona": persona}
            user, created = User.objects.get_or_create(username=username, defaults=defaults)
            if created or reset:
                if reset:
                    for campo, valor in defaults.items():
                        setattr(user, campo, valor)
                user.set_password(password)
                user.save()

        productos = [
            ("Papa Desirée", "PAPA", "Desirée", 500, 12000),
            ("Papa Cardinal", "PAPA", "Cardinal", 300, 11000),
            ("Trigo", "TRIGO", "", 200, 18000),
            ("Avena", "AVENA", "", 100, 15000),
            ("Maíz", "MAIZ", "", 100, 16000),
        ]
        for nombre, cat, variedad, stock, precio in productos:
            ProductoVenta.objects.get_or_create(nombre=nombre, defaults={
                "categoria": cat, "variedad": variedad, "unidad_medida": "SACO",
                "cantidad_disponible": Decimal(stock), "stock_minimo": Decimal(20),
                "precio_referencia": precio, "peso_saco_kg": Decimal("25")})

        InsumoAgricola.objects.get_or_create(nombre="Urea", defaults={
            "tipo": "FERTILIZANTE", "unidad_medida": "SACO",
            "cantidad_disponible": Decimal(80), "dosis_por_hectarea": Decimal("6")})
        InsumoAgricola.objects.get_or_create(nombre="Semilla de papa", defaults={
            "tipo": "SEMILLA", "unidad_medida": "SACO",
            "cantidad_disponible": Decimal(400), "dosis_por_hectarea": Decimal("60")})

        Cliente.objects.get_or_create(rut="11111111-1", defaults={
            "nombre": "Feria Lo Valledor", "tipo": "MAYORISTA", "telefono": "+56911111111",
            "comuna": "Pedro Aguirre Cerda", "limite_credito": 2000000})
        Cliente.objects.get_or_create(rut="22222222-2", defaults={
            "nombre": "Almacén Don Pedro", "tipo": "MINORISTA", "telefono": "+56922222222",
            "comuna": "Chillán"})
        Proveedor.objects.get_or_create(rut="44444444-4", defaults={
            "nombre": "Agroinsumos del Sur", "rubro": "Fertilizantes"})

        for cuerpo, nombre in [(33333333, "Juan Pérez"), (15234567, "Luisa Campos"),
                               (16345678, "José Navarro")]:
            Trabajador.objects.get_or_create(rut=rut(cuerpo), defaults={
                "nombre": nombre, "tipo_contrato": "TEMPORERO", "cargo": "Temporero",
                "tarifa_diaria": 25000})

        self.stdout.write(self.style.SUCCESS("Datos demo listos."))
        self.stdout.write(f"{'USUARIO':<13}{'ROL':<12}{'CLAVE':<14}NOTA")
        for username, rol, *_rest in USUARIOS_DEMO:
            desc = _rest[2]
            self.stdout.write(f"{username:<13}{rol:<12}{password:<14}{desc}")
