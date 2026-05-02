# core/middleware.py
"""
Middleware de restriction admin pour le superadmin.

Le superadmin n'a accès dans /admin/ qu'aux URLs d'authentification
(utilisateurs, groupes) et aux URLs techniques (login, logout, etc.).
Toute autre URL /admin/xxx/ lui est interdite → redirection.
"""
from django.shortcuts import redirect


# Préfixes /admin/ autorisés pour le superadmin
_ADMIN_ALLOWED_PREFIXES = (
    '/admin/auth/',           # Users & Groups
    '/admin/login',           # Connexion
    '/admin/logout',          # Déconnexion
    '/admin/password_change', # Changement de mot de passe
    '/admin/jsi18n',          # Traductions JS
    '/admin/autocomplete',    # Autocomplete
    '/admin/r/',              # Redirections d'objets
    '/admin/redirect/',       # Notre propre redirect
)

_ADMIN_ALLOWED_EXACT = frozenset([
    '/admin/',
    '/admin/index/',
])


class SuperadminAdminRestrictionMiddleware:
    """
    Bloque l'accès du superadmin aux pages Django admin non-système.
    S'applique uniquement sur les chemins /admin/.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_block(request):
            return redirect('/admin/auth/user/')
        return self.get_response(request)

    def _should_block(self, request):
        path = request.path

        # N'intervient que sur /admin/
        if not path.startswith('/admin/'):
            return False

        # Pas encore authentifié → laisser passer (login etc.)
        if not request.user.is_authenticated:
            return False

        # Seul le superadmin est concerné
        from core.roles import is_superadmin
        if not is_superadmin(request.user):
            return False

        # Chemins exacts autorisés
        if path in _ADMIN_ALLOWED_EXACT:
            return False

        # Préfixes autorisés
        if any(path.startswith(prefix) for prefix in _ADMIN_ALLOWED_PREFIXES):
            return False

        # Tout le reste est bloqué
        return True
