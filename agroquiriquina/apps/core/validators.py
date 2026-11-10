from django.core.exceptions import ValidationError


def normalizar_rut(value: str) -> str:
    """'12.345.678-5' -> '12345678-5'."""
    rut = str(value).replace(".", "").replace("-", "").replace(" ", "").upper()
    return f"{rut[:-1]}-{rut[-1]}" if len(rut) > 1 else rut


def validar_rut(value: str) -> None:
    rut = normalizar_rut(value)
    try:
        cuerpo, dv = rut.split("-")
    except ValueError:
        raise ValidationError("RUT inválido.")
    if not cuerpo.isdigit():
        raise ValidationError("RUT inválido.")
    suma, mult = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mult
        mult = 2 if mult == 7 else mult + 1
    resto = 11 - (suma % 11)
    esperado = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    if dv != esperado:
        raise ValidationError("RUT inválido (dígito verificador incorrecto).")
