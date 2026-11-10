from rest_framework import serializers

from apps.core.validators import normalizar_rut

from .models import Cliente, Persona, Proveedor, Trabajador, User


class PersonaBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ["id", "rut", "nombre", "telefono", "email", "direccion",
                  "comuna", "region", "updated_at", "is_deleted"]
        read_only_fields = ["updated_at"]
        # UUID generado por el cliente offline
        extra_kwargs = {"id": {"read_only": False, "required": False}}

    def to_internal_value(self, data):
        # Normaliza el RUT antes de validar unicidad ("12.345.678-5" -> "12345678-5")
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if data.get("rut"):
            data["rut"] = normalizar_rut(data["rut"])
        return super().to_internal_value(data)


class ClienteSerializer(PersonaBaseSerializer):
    class Meta(PersonaBaseSerializer.Meta):
        model = Cliente
        fields = PersonaBaseSerializer.Meta.fields + ["tipo", "razon_social", "limite_credito"]


class ProveedorSerializer(PersonaBaseSerializer):
    class Meta(PersonaBaseSerializer.Meta):
        model = Proveedor
        fields = PersonaBaseSerializer.Meta.fields + ["rubro", "condiciones_pago"]


class TrabajadorSerializer(PersonaBaseSerializer):
    class Meta(PersonaBaseSerializer.Meta):
        model = Trabajador
        fields = PersonaBaseSerializer.Meta.fields + [
            "tipo_contrato", "cargo", "tarifa_diaria", "fecha_ingreso", "activo"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email",
                  "rol", "persona", "is_active", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
