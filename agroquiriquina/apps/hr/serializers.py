from rest_framework import serializers

from .models import Desempeno, Remuneracion


class DesempenoSerializer(serializers.ModelSerializer):
    monto = serializers.DecimalField(max_digits=14, decimal_places=0, read_only=True)

    class Meta:
        model = Desempeno
        fields = ["id", "trabajador", "fecha", "labor", "cantidad", "unidad",
                  "tarifa_unitaria", "monto", "remuneracion", "device_id",
                  "updated_at", "is_deleted"]
        read_only_fields = ["remuneracion", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": False, "required": False},
            # Si no se envía, se usa la tarifa diaria del trabajador (útil para JORNAL).
            "tarifa_unitaria": {"required": False},
        }

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que 0.")
        return value

    def validate(self, attrs):
        if self.instance is None and attrs.get("tarifa_unitaria") is None:
            tarifa = attrs["trabajador"].tarifa_diaria
            if not tarifa:
                raise serializers.ValidationError(
                    {"tarifa_unitaria": "Indica la tarifa o define la tarifa diaria del trabajador."})
            attrs["tarifa_unitaria"] = tarifa
        return attrs


class RemuneracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remuneracion
        fields = ["id", "trabajador", "periodo_inicio", "periodo_fin", "total_produccion",
                  "bonos", "descuentos", "total_liquido", "estado", "updated_at"]
        read_only_fields = ["total_produccion", "total_liquido", "estado", "updated_at"]

    def validate(self, attrs):
        inicio = attrs.get("periodo_inicio", getattr(self.instance, "periodo_inicio", None))
        fin = attrs.get("periodo_fin", getattr(self.instance, "periodo_fin", None))
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError({"periodo_fin": "Debe ser posterior al inicio."})
        if self.instance and self.instance.estado != Remuneracion.Estado.BORRADOR:
            raise serializers.ValidationError("Solo se pueden editar remuneraciones en borrador.")
        return attrs

    def create(self, validated_data):
        rem = super().create(validated_data)
        rem.calcular()
        return rem

    def update(self, instance, validated_data):
        rem = super().update(instance, validated_data)
        rem.calcular()
        return rem
