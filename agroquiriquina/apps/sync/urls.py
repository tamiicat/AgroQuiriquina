from django.urls import path

from .views import CatalogoView, ClienteBulkView, DesempenoBulkView, VentaBulkView

urlpatterns = [
    path("ventas/bulk/", VentaBulkView.as_view(), name="sync-ventas-bulk"),
    path("desempenos/bulk/", DesempenoBulkView.as_view(), name="sync-desempenos-bulk"),
    path("clientes/bulk/", ClienteBulkView.as_view(), name="sync-clientes-bulk"),
    path("catalogo/", CatalogoView.as_view(), name="sync-catalogo"),
]
