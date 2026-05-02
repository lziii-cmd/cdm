# frontend/views/referentiels.py
from django.core.paginator import Paginator
from .base import FrontendView


class FournisseursListView(FrontendView):
    template_name = 'v2/misc/fournisseurs.html'
    active_page = 'fournisseurs'
    inventory_view = True
    agent_perm_key = 'perm_fournisseurs'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from core.models import Fournisseur
            qs = Fournisseur.objects.order_by('raison_sociale')
            q = self.request.GET.get('q', '')
            if q:
                qs = qs.filter(raison_sociale__icontains=q)
            ctx['fournisseurs'] = qs
            ctx['q'] = q
        except Exception:
            ctx['fournisseurs'] = []
            ctx['q'] = ''
        return ctx


class DonateursListView(FrontendView):
    template_name = 'v2/misc/donateurs.html'
    active_page = 'donateurs'
    inventory_view = True
    agent_perm_key = 'perm_donateurs'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from core.models import Donateur
            ctx['donateurs'] = Donateur.objects.order_by('raison_sociale')
        except Exception:
            ctx['donateurs'] = []
        return ctx


class DepotsListView(FrontendView):
    template_name = 'v2/misc/depots.html'
    active_page = 'depots'
    inventory_view = True
    agent_perm_key = 'perm_depots'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from core.models import Depot
            ctx['depots'] = Depot.objects.order_by('identifiant')
        except Exception:
            ctx['depots'] = []
        return ctx


class ServicesListView(FrontendView):
    template_name = 'v2/misc/services.html'
    active_page = 'services'
    inventory_view = True
    agent_perm_key = 'perm_services'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from core.models import Service
            ctx['services'] = Service.objects.order_by('code')
        except Exception:
            ctx['services'] = []
        return ctx


class UnitesListView(FrontendView):
    template_name = 'v2/misc/unites.html'
    active_page = 'unites'
    inventory_view = True
    agent_perm_key = 'perm_unites'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from catalog.models import Unite
            ctx['unites'] = Unite.objects.order_by('libelle')
        except Exception:
            ctx['unites'] = []
        return ctx
