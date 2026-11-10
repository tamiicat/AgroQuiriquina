from rest_framework import serializers

from .models import DetalleVenta, Despacho, Pago, Venta
from .services import registrar_venta

ID_OFFLINE = {"id": {"read_only": False, "required": False}}  # UUID generado en el móvil


class DetalleVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleVenta
        fields = ["id", "producto", "cantidad", "precio_unitario", "subtotal"]
        read_only_fields = ["subtotal"]
        extra_kwargs = ID_OFFLINE

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que 0.")
        return value


class PagoNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = ["id", "monto", "estado", "metodo", "fecha_vencimiento", "fecha_pago"]
        extra_kwargs = ID_OFFLINE


class DespachoNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despacho
        fields = ["id", "fecha", "hora", "direccion", "comuna", "estado",
                  "transportista", "patente", "observaciones"]
        extra_kwargs = ID_OFFLINE


class PagoSerializer(serializers.ModelSerializer):
    """Uso independiente (registrar un abono sobre una venta existente)."""
    class Meta:
        model = Pago
        fields = ["id", "venta", "monto", "estado", "metodo",
                  "fecha_vencimiento", "fecha_pago", "updated_at", "is_deleted"]
        read_only_fields = ["updated_at"]
        extra_kwargs = ID_OFFLINE


class DespachoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despacho
        fields = ["id", "venta", "fecha", "hora", "direccion", "comuna", "estado",
                  "transportista", "patente", "observaciones", "updated_at", "is_deleted"]
        read_only_fields = ["updated_at"]
        extra_kwargs = ID_OFFLINE


class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, allow_empty=False)
    pagos = PagoNestedSerializer(many=True, required=False)
    despacho = DespachoNestedSerializer(required=False)
    estado_pago = serializers.CharField(read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=14, decimal_places=0, read_only=True)

    class Meta:
        model = Venta
        fields = ["id", "cliente", "vendedor", "fecha", "estado", "total", "observaciones",
                  "device_id", "requiere_revision", "synced_at",
                  "detalles", "pagos", "despacho", "estado_pago", "saldo_pendiente",
                  "updated_at", "is_deleted"]
        read_only_fields = ["vendedor", "estado", "total", "requiere_revision",
                            "synced_at", "updated_at"]
        extra_kwargs = ID_OFFLINE

    def validate_id(self, value):
        if self.instance is None and Venta.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Ya existe una venta con este id.")
        return value

    def create(self, validated_data):
        return registrar_venta(validated_data)   # vendedor llega vía serializer.save(vendedor=...)
