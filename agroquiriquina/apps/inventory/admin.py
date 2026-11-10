from django.contrib import admin

from .models import InsumoAgricola, MovimientoStock, ProductoVenta


@admin.register(ProductoVenta)
class ProductoVentaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "cantidad_disponible", "unidad_medida", "precio_referencia")
    list_filter = ("categoria", "activo")
    search_fields = ("nombre", "variedad")


@admin.register(InsumoAgricola)
class InsumoAgricolaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "cantidad_disponible", "unidad_medida", "dosis_por_hectarea")
    list_filter = ("tipo",)
    search_fields = ("nombre",)


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ("created_at", "item", "tipo", "cantidad", "motivo", "usuario")
    list_filter = ("tipo",)
    readonly_fields = [f.name for f in MovimientoStock._meta.fields]
