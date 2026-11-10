import logging
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ADMIN, HasRole, SUPERVISOR, VENDEDOR
from apps.core.utils import parse_updated_since
from apps.hr.models import Desempeno
from apps.hr.serializers import DesempenoSerializer
from apps.inventory.models import ProductoVenta
from apps.inventory.serializers import ProductoVentaSerializer
from apps.sales.models import Venta
from apps.sales.serializers import VentaSerializer
from apps.users.models import Cliente, Trabajador
from apps.users.serializers import ClienteSerializer, TrabajadorSerializer

logger = logging.getLogger(__name__)

MAX_LOTE = 500


def _a_uuid(valor):
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError, TypeError):
        return None


class BulkUploadView(APIView):
    """
    Base para subida masiva offline.

    Entrada:  [ {...}, {...} ]   o   {"<clave>": [ {...}, ... ]}   (máx. 500 ítems)
    Reglas:
      * Cada ítem DEBE traer `id` (UUID generado en el dispositivo) -> idempotencia.
      * Cada ítem se procesa en su propia transacción: uno inválido no bloquea al resto.
      * Si el `id` ya existe en el servidor -> status "duplicate" (no se vuelve a crear).
    Respuesta: 200 si todo OK, 207 si hubo algún error.
    """
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = None
    model = None
    clave = "items"

    def get_save_kwargs(self, request):
        return {}

    def _extraer_items(self, data):
        if isinstance(data, list):
            return data
        if hasattr(data, "get"):
            items = data.get(self.clave)
            if isinstance(items, list):
                return items
        return None

    def post(self, request):
        items = self._extraer_items(request.data)
        if items is None:
            return Response(
                {"detail": f"Envía una lista JSON o un objeto con la clave '{self.clave}'."},
                status=status.HTTP_400_BAD_REQUEST)
        if len(items) > MAX_LOTE:
            return Response({"detail": f"Máximo {MAX_LOTE} registros por lote."},
                            status=status.HTTP_400_BAD_REQUEST)

        ids = {_a_uuid(i.get("id")) for i in items if isinstance(i, dict)} - {None}
        existentes = set(self.model.objects.filter(pk__in=ids).values_list("pk", flat=True))
        save_kwargs = self.get_save_kwargs(request)

        resultados, conteo = [], {"created": 0, "duplicate": 0, "error": 0}
        for idx, item in enumerate(items):
            res = {"index": idx, "id": None, "status": "error"}
            if not isinstance(item, dict):
                res["errors"] = {"detail": "Cada registro debe ser un objeto JSON."}
            elif (item_id := _a_uuid(item.get("id"))) is None:
                res["errors"] = {"id": "Requerido: UUID generado en el dispositivo."}
            else:
                res["id"] = str(item_id)
                if item_id in existentes:
                    res["status"] = "duplicate"
                else:
                    ser = self.serializer_class(data=item, context={"request": request})
                    if ser.is_valid():
                        try:
                            with transaction.atomic():
                                ser.save(**save_kwargs)
                            res["status"] = "created"
                            existentes.add(item_id)   # duplicados dentro del mismo lote
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("Error guardando registro offline %s", item_id)
                            res["errors"] = {"detail": str(exc)}
                    else:
                        res["errors"] = ser.errors
            conteo[res["status"]] += 1
            resultados.append(res)

        http = status.HTTP_200_OK if conteo["error"] == 0 else status.HTTP_207_MULTI_STATUS
        return Response({
            "resumen": {"recibidos": len(items), "creados": conteo["created"],
                        "duplicados": conteo["duplicate"], "errores": conteo["error"]},
            "resultados": resultados,
            "server_time": timezone.now(),
        }, status=http)


class VentaBulkView(BulkUploadView):
    serializer_class = VentaSerializer
    model = Venta
    clave = "ventas"
    write_roles = [VENDEDOR]

    def get_save_kwargs(self, request):
        return {"vendedor": request.user, "synced_at": timezone.now()}


class DesempenoBulkView(BulkUploadView):
    serializer_class = DesempenoSerializer
    model = Desempeno
    clave = "desempenos"
    write_roles = [SUPERVISOR]

    def get_save_kwargs(self, request):
        return {"registrado_por": request.user}


class ClienteBulkView(BulkUploadView):
    serializer_class = ClienteSerializer
    model = Cliente
    clave = "clientes"
    write_roles = [VENDEDOR]


class CatalogoView(APIView):
    """
    Descarga de catálogo para trabajar offline, SIN paginación, en una sola llamada.
    GET /sync/catalogo/?updated_since=<ISO8601>
    Guarda `server_time` y úsalo como `updated_since` en la próxima sincronización.
    Incluye borrados lógicos (is_deleted=true) cuando se usa updated_since.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        since = parse_updated_since(request)
        rol = request.user.rol
        es_admin = request.user.is_superuser or rol == ADMIN

        def filtrar(qs):
            return qs.filter(updated_at__gt=since) if since else qs.filter(is_deleted=False)

        data = {"server_time": timezone.now()}
        if es_admin or rol == VENDEDOR:
            data["clientes"] = ClienteSerializer(filtrar(Cliente.objects.all()), many=True).data
            data["productos"] = ProductoVentaSerializer(
                filtrar(ProductoVenta.objects.all()), many=True).data
        if es_admin or rol == SUPERVISOR:
            data["trabajadores"] = TrabajadorSerializer(
                filtrar(Trabajador.objects.all()), many=True).data
        return Response(data)
