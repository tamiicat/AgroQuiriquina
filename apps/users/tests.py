from django.core.management import call_command
from rest_framework.test import APITestCase

from .models import Trabajador, User

PASSWORD = "Cambiar123!"


class UsuariosDemoTests(APITestCase):
    """Verifica que los usuarios de seed_demo funcionen y que el RBAC se cumpla."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def _login(self, username, password=PASSWORD):
        return self.client.post("/api/v1/auth/token/",
                                {"username": username, "password": password}, format="json")

    def _auth(self, username):
        token = self._login(username).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_login_y_rol_de_cada_usuario(self):
        esperados = {"admin": "ADMIN", "gerente": "ADMIN", "vendedor1": "VENDEDOR",
                     "vendedor2": "VENDEDOR", "supervisor1": "SUPERVISOR",
                     "supervisor2": "SUPERVISOR"}
        for username, rol in esperados.items():
            with self.subTest(username=username):
                r = self._login(username)
                self.assertEqual(r.status_code, 200, r.data)
                self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
                self.assertEqual(self.client.get("/api/v1/me/").data["rol"], rol)

    def test_usuario_inactivo_no_puede_entrar(self):
        self.assertEqual(self._login("inactivo").status_code, 401)

    def test_clave_incorrecta(self):
        self.assertEqual(self._login("admin", "otra-clave").status_code, 401)

    def test_supervisores_estan_vinculados_a_trabajador(self):
        sup = User.objects.get(username="supervisor1")
        self.assertTrue(Trabajador.objects.filter(pk=sup.persona_id).exists())

    def test_matriz_de_permisos(self):
        # (usuario, url, status esperado)
        casos = [
            ("vendedor1", "/api/v1/clientes/", 200),
            ("vendedor1", "/api/v1/trabajadores/", 403),
            ("vendedor1", "/api/v1/finanzas/cuentas-por-cobrar/", 403),
            ("vendedor1", "/api/v1/usuarios/", 403),
            ("supervisor1", "/api/v1/trabajadores/", 200),
            ("supervisor1", "/api/v1/clientes/", 403),
            ("supervisor1", "/api/v1/remuneraciones/", 403),
            ("gerente", "/api/v1/usuarios/", 200),
            ("gerente", "/api/v1/finanzas/cuentas-por-cobrar/", 200),
            ("admin", "/api/v1/remuneraciones/", 200),
        ]
        for username, url, status in casos:
            with self.subTest(username=username, url=url):
                self._auth(username)
                self.assertEqual(self.client.get(url).status_code, status)

    def test_seed_es_idempotente_y_reset_restablece_clave(self):
        call_command("seed_demo", verbosity=0)
        self.assertEqual(User.objects.filter(username="admin").count(), 1)
        u = User.objects.get(username="vendedor1")
        u.set_password("otra-clave-123")
        u.save()
        call_command("seed_demo", "--reset", verbosity=0)
        self.assertEqual(self._login("vendedor1").status_code, 200)
