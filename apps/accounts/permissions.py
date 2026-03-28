from rest_framework.permissions import BasePermission


class IsProducteur(BasePermission):
    """Autorise uniquement les utilisateurs avec le rôle producteur."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'producteur'
        )


class IsAcheteur(BasePermission):
    """Autorise uniquement les acheteurs."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'acheteur'
        )


class IsProducteurActif(BasePermission):
    """Autorise uniquement les producteurs avec statut actif."""
    message = "Votre compte producteur est en attente de validation."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role != 'producteur':
            return False
        try:
            return request.user.profil_producteur.statut == 'actif'
        except Exception:
            return False


class IsSuperAdmin(BasePermission):
    """Autorise uniquement les superadmins."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (
                request.user.is_superuser or
                request.user.is_staff or
                getattr(request.user, 'role', '') == 'superadmin'
            )
        )
