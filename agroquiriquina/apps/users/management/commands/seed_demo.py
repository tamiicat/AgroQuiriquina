from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import InsumoAgricola, ProductoVenta
from apps.users.models import Cliente, Proveedor, Rol, Trabajador, User

PASSWORD = "Cambiar123!"


class Command(BaseCommand):
    help = "Crea usuarios (admin/vendedor1/supervisor1) y datos de ejemplo para probar la API."

    @transaction.atomic
    def handle(self, *args, **options):
        for username, rol, es_admin in [
            ("admin", Rol.ADMINISTRADOR, True),
            ("vendedor1", Rol.VENDEDOR, False),
            ("supervisor1", Rol.SUPERVISOR_TERRENO, False),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"rol": rol, "is_staff": es_admin, "is_superuser": es_admin,
                          "email": f"{username}@agroquiriquina.local"},
            )
            if created:
                user.set_password(PASSWORD)
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
        Trabajador.objects.get_or_create(rut="33333333-3", defaults={
            "nombre": "Juan Pérez", "tipo_contrato": "TEMPORERO", "tarifa_diaria": 25000})

        self.stdout.write(self.style.SUCCESS(
            f"Datos demo listos. Usuarios: admin / vendedor1 / supervisor1  (clave: {PASSWORD})"))
