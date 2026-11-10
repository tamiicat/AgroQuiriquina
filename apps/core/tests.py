from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .validators import normalizar_rut, validar_rut


class RutTests(SimpleTestCase):
    def test_rut_valido_con_puntos(self):
        validar_rut("11.111.111-1")

    def test_rut_invalido(self):
        with self.assertRaises(ValidationError):
            validar_rut("11.111.111-2")

    def test_normalizar(self):
        self.assertEqual(normalizar_rut("11.111.111-1"), "11111111-1")
