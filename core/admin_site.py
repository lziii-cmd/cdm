# core/admin_site.py
"""
AdminSite personnalisé pour ENSMG.

Le superadmin (is_superuser=True sans groupe inventaire) ne voit que
l'application "auth" dans la sidebar Django admin.
"""
from django.contrib.admin import AdminSite
from core.roles import is_superadmin

# Apps autorisées dans l'admin pour un superadmin pur
SUPERADMIN_ALLOWED_APPS = frozenset(['auth'])


class ENSMGAdminSite(AdminSite):
    site_header = 'ENSMG — Administration'
    site_title  = 'ENSMG Admin'
    index_title = 'Administration système'

    def get_app_list(self, request, app_label=None):
        """Filtre la liste des apps pour le superadmin : auth uniquement."""
        app_list = super().get_app_list(request, app_label)
        if is_superadmin(request.user):
            app_list = [
                app for app in app_list
                if app['app_label'] in SUPERADMIN_ALLOWED_APPS
            ]
        return app_list
