from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Les signaux d'audit sont gérés par AuditConfig.ready() dans audit/apps.py

        # Remplace la classe du site admin par défaut pour filtrer
        # les apps visibles selon le rôle (superadmin → auth uniquement).
        # Le monkey-patch préserve le registre _registry existant.
        from django.contrib import admin
        from core.admin_site import ENSMGAdminSite
        admin.site.__class__ = ENSMGAdminSite
