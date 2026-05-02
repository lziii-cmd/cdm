# frontend/views/dashboard.py
from django.db.models import Count, Sum
from .base import FrontendView
from core.roles import ROLE_SUPERADMIN


class DashboardView(FrontendView):
    template_name = 'v2/dashboard.html'
    active_page = 'dashboard'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if ctx.get('is_superadmin'):
            self._load_superadmin_context(ctx)
        else:
            self._load_inventory_context(ctx)

        return ctx

    def _load_superadmin_context(self, ctx):
        """Données système pour le superadmin."""
        try:
            from django.contrib.auth import get_user_model
            from django.contrib.auth.models import Group
            from core.models import Exercice
            User = get_user_model()
            ctx['nb_utilisateurs'] = User.objects.filter(is_active=True).count()
            ctx['nb_groupes']      = Group.objects.count()
            ctx['nb_exercices']    = Exercice.objects.count()
            ctx['nb_superadmins']  = User.objects.filter(is_superuser=True).count()
            ctx['nb_chefs']        = User.objects.filter(groups__name='Chef de service').count()
            ctx['nb_agents']       = User.objects.filter(groups__name='Agent simple').count()
        except Exception:
            ctx['nb_utilisateurs'] = 0
            ctx['nb_groupes']      = 0
            ctx['nb_exercices']    = 0
            ctx['nb_superadmins']  = 0
            ctx['nb_chefs']        = 0
            ctx['nb_agents']       = 0

    def _load_inventory_context(self, ctx):
        """Données inventaire pour le chef de service et les agents."""
        try:
            from core.models import Depot, Fournisseur, Exercice
            from inventory.models import StockCourant
            from catalog.models import Categorie

            ctx['nb_fournisseurs']  = Fournisseur.objects.count()
            ctx['nb_depots']        = Depot.objects.count()
            ctx['nb_exercices']     = Exercice.objects.count()
            ctx['nb_lignes_stock']  = StockCourant.objects.count()
            ctx['categories'] = list(
                Categorie.objects.annotate(
                    nb_matieres=Count('sous_categories__matieres')
                ).values('code', 'libelle', 'nb_matieres')[:10]
            )
            ctx['top_matieres'] = list(
                StockCourant.objects.values(
                    'matiere__code_court', 'matiere__designation'
                ).annotate(total_qty=Sum('quantite')).order_by('-total_qty')[:8]
            )
        except Exception:
            ctx['nb_fournisseurs'] = 0
            ctx['nb_depots']       = 0
            ctx['nb_exercices']    = 0
            ctx['nb_lignes_stock'] = 0
            ctx['categories']      = []
            ctx['top_matieres']    = []
