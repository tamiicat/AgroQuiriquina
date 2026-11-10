from django.contrib import admin

from .models import Desempeno, Remuneracion


@admin.register(Desempeno)
class DesempenoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "trabajador", "labor", "cantidad", "unidad", "tarifa_unitaria", "remuneracion")
    list_filter = ("labor", "fecha")
    search_fields = ("trabajador__nombre", "trabajador__rut")


@admin.register(Remuneracion)
class RemuneracionAdmin(admin.ModelAdmin):
    list_display = ("trabajador", "periodo_inicio", "periodo_fin", "total_produccion",
                    "bonos", "descuentos", "total_liquido", "estado")
    list_filter = ("estado",)
    search_fields = ("trabajador__nombre", "trabajador__rut")
