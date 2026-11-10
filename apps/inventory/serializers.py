from rest_framework import serializers

from .models import InsumoAgricola, MovimientoStock, ProductoVenta


class ProductoVentaSerializer(serializers.ModelSerializer):
    bajo_stock_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductoVenta
        fields = ["id", "nombre", "categoria", "variedad", "cantidad_disponible",
                  "unidad_medida", "stock_minimo", "bajo_stock_minimo",
                  "precio_referencia", "peso_saco_kg", "activo", "updated_at", "is_deleted"]
        # El stock solo cambia vía movimientos (POST .../movimiento/) o ventas.
        read_only_fields = ["cantidad_disponible", "updated_at"]


class InsumoAgricolaSerializer(serializers.ModelSerializer):
    bajo_stock_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = InsumoAgricola
        fields = ["id", "nombre", "tipo", "cantidad_disponible", "unidad_medida",
                  "stock_minimo", "bajo_stock_minimo", "dosis_por_hectarea",
                  "activo", "updated_at", "is_deleted"]
        read_only_fields = ["cantidad_disponible", "updated_at"]


class MovimientoInputSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=MovimientoStock.Tipo.choices)
    cantidad = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)
    motivo = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class MovimientoStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoStock
        fields = ["id", "item", "tipo", "cantidad", "motivo", "referencia", "usuario", "created_at"]
        read_only_fields = fields
