from django.contrib import admin

from .models import DetalleVenta, Despacho, Pago, Venta


class DetalleInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ("subtotal",)


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0


class DespachoInline(admin.StackedInline):
    model = Despacho
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha", "total", "estado", "requiere_revision", "vendedor")
    list_filter = ("estado", "requiere_revision")
    search_fields = ("cliente__nombre", "cliente__rut")
    inlines = [DetalleInline, PagoInline, DespachoInline]


@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "hora", "venta", "direccion", "estado")
    list_filter = ("estado", "fecha")
