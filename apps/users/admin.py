from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Cliente, Proveedor, Trabajador, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Rol y persona", {"fields": ("rol", "persona")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Rol", {"fields": ("rol",)}),)
    list_display = ("username", "email", "rol", "is_active")
    list_filter = DjangoUserAdmin.list_filter + ("rol",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "tipo", "telefono", "limite_credito", "is_deleted")
    search_fields = ("nombre", "rut", "razon_social")
    list_filter = ("tipo", "is_deleted")


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "rubro", "telefono")
    search_fields = ("nombre", "rut", "rubro")


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "tipo_contrato", "tarifa_diaria", "activo")
    search_fields = ("nombre", "rut")
    list_filter = ("tipo_contrato", "activo")
