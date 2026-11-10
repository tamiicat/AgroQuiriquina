from rest_framework.permissions import SAFE_METHODS, BasePermission

# Valores idénticos a users.models.Rol (se usan como strings para evitar imports circulares)
ADMIN = "ADMIN"
VENDEDOR = "VENDEDOR"
SUPERVISOR = "SUPERVISOR"


class HasRole(BasePermission):
    """
    RBAC declarativo. Cada vista define:
        read_roles  -> roles que pueden leer (GET/HEAD/OPTIONS). Si no existe, usa write_roles.
        write_roles -> roles que pueden escribir.
    El rol ADMIN (y los superusuarios) siempre tienen acceso.
    """
    message = "Tu rol no tiene permiso para esta operación."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or getattr(user, "rol", None) == ADMIN:
            return True
        write_roles = getattr(view, "write_roles", [])
        if request.method in SAFE_METHODS:
            roles = getattr(view, "read_roles", write_roles)
        else:
            roles = write_roles
        return user.rol in roles
