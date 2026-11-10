from decimal import Decimal

from django.db import transaction

from .models import ItemBodega, MovimientoStock


class StockInsuficiente(Exception):
    pass


@transaction.atomic
def aplicar_movimiento(item_id, tipo, cantidad, usuario=None, motivo="",
                       referencia=None, permitir_faltante=False):
    """
    Único punto de entrada para modificar stock (bloquea la fila con SELECT ... FOR UPDATE).

    - ENTRADA: suma `cantidad`.
    - SALIDA : resta `cantidad`. Si no alcanza:
        * permitir_faltante=False -> lanza StockInsuficiente.
        * permitir_faltante=True  -> descuenta lo que haya (queda en 0) y devuelve el faltante.
          (Caso ventas offline: la venta ya ocurrió físicamente.)
    - AJUSTE : `cantidad` es el NUEVO stock total (conteo físico).
    Devuelve (movimiento, faltante).
    """
    item = ItemBodega.objects.select_for_update().get(pk=item_id)
    cantidad = Decimal(cantidad)
    faltante = Decimal("0")

    if tipo == MovimientoStock.Tipo.ENTRADA:
        nuevo = item.cantidad_disponible + cantidad
        registrado = cantidad
    elif tipo == MovimientoStock.Tipo.SALIDA:
        nuevo = item.cantidad_disponible - cantidad
        registrado = cantidad
        if nuevo < 0:
            if not permitir_faltante:
                raise StockInsuficiente(
                    f"Stock insuficiente de '{item.nombre}': hay {item.cantidad_disponible}, "
                    f"se pidió {cantidad}."
                )
            faltante = -nuevo
            registrado = item.cantidad_disponible
            nuevo = Decimal("0")
            motivo = (motivo + f" | FALTANTE {faltante}").strip(" |")
    elif tipo == MovimientoStock.Tipo.AJUSTE:
        if cantidad < 0:
            raise StockInsuficiente("El stock ajustado no puede ser negativo.")
        registrado = abs(cantidad - item.cantidad_disponible)
        nuevo = cantidad
    else:
        raise ValueError(f"Tipo de movimiento inválido: {tipo}")

    item.cantidad_disponible = nuevo
    item.save(update_fields=["cantidad_disponible", "updated_at"])
    mov = MovimientoStock.objects.create(
        item=item, tipo=tipo, cantidad=registrado, motivo=motivo[:200],
        referencia=referencia, usuario=usuario,
    )
    return mov, faltante
