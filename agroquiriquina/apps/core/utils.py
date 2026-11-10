from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError


def parse_updated_since(request):
    """Lee ?updated_since=<ISO8601>. Devuelve datetime aware o None."""
    raw = request.query_params.get("updated_since")
    if not raw:
        return None
    # En una URL el '+' del huso horario llega como espacio.
    dt = parse_datetime(raw.strip().replace(" ", "+"))
    if dt is None:
        raise ValidationError({"updated_since": "Formato inválido. Usa ISO 8601."})
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt
