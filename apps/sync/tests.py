import uuid
from decimal import Decimal

from rest_framework.test import APITestCase

from apps.inventory.models import ProductoVenta
from apps.users.models import Cliente, Rol, User


class BulkVentasTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("vend", password="x12345678", rol=Rol.VENDEDOR)
        self.client.force_authenticate(self.user)
        self.cliente = Cliente.objects.create(rut="11111111-1", nombre="Cliente Test")
        self.producto = ProductoVenta.objects.create(
            nombre="Papa", categoria="PAPA", cantidad_disponible=Decimal("10"))

    def _venta(self, vid, cantidad="5"):
        return {
            "id": str(vid), "cliente": str(self.cliente.pk),
            "fecha": "2026-01-10T10:00:00-03:00",
            "detalles": [{"producto": str(self.producto.pk), "cantidad": cantidad,
                          "precio_unitario": 10000}],
        }

    def test_lote_idempotente_y_stock(self):
        vid = uuid.uuid4()
        url = "/api/v1/sync/ventas/bulk/"
        r1 = self.client.post(url, [self._venta(vid)], format="json")
        self.assertEqual(r1.status_code, 200, r1.data)
        self.assertEqual(r1.data["resumen"]["creados"], 1)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.cantidad_disponible, Decimal("5"))

        r2 = self.client.post(url, [self._venta(vid)], format="json")
        self.assertEqual(r2.data["resumen"]["duplicados"], 1)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.cantidad_disponible, Decimal("5"))  # no se descuenta 2 veces

    def test_stock_insuficiente_marca_revision_y_no_rechaza(self):
        vid = uuid.uuid4()
        r = self.client.post("/api/v1/sync/ventas/bulk/", [self._venta(vid, "15")], format="json")
        self.assertEqual(r.data["resumen"]["creados"], 1)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.cantidad_disponible, Decimal("0"))
        from apps.sales.models import Venta
        v = Venta.objects.get(pk=vid)
        self.assertTrue(v.requiere_revision)
        self.assertEqual(v.total, Decimal("150000"))

    def test_item_invalido_no_bloquea_los_demas(self):
        malo = self._venta(uuid.uuid4())
        malo["detalles"] = []
        r = self.client.post("/api/v1/sync/ventas/bulk/",
                             [malo, self._venta(uuid.uuid4())], format="json")
        self.assertEqual(r.status_code, 207)
        self.assertEqual(r.data["resumen"]["errores"], 1)
        self.assertEqual(r.data["resumen"]["creados"], 1)

    def test_supervisor_no_puede_subir_ventas(self):
        sup = User.objects.create_user("sup", password="x12345678", rol=Rol.SUPERVISOR_TERRENO)
        self.client.force_authenticate(sup)
        r = self.client.post("/api/v1/sync/ventas/bulk/", [self._venta(uuid.uuid4())], format="json")
        self.assertEqual(r.status_code, 403)
