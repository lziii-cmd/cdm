# frontend/views/agents.py
"""
Vues de gestion des agents simples — accessibles au chef de service uniquement.
"""
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect

from core.models.agent_permission import AgentPermission
from core.roles import ROLE_CHEF_SERVICE, get_user_role
from .base import FrontendView

logger = logging.getLogger(__name__)
User = get_user_model()


class ChefServiceRequiredMixin:
    """Restreint la vue au chef de service uniquement."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/admin/login/')
        if get_user_role(request.user) != ROLE_CHEF_SERVICE:
            messages.error(request, "Cette section est réservée au chef de service.")
            return redirect('frontend:dashboard')
        return super().dispatch(request, *args, **kwargs)


class AgentListView(ChefServiceRequiredMixin, FrontendView):
    """Liste des agents simples — vue chef de service."""
    template_name = 'v2/misc/gestion_agents.html'
    active_page   = 'gestion_agents'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            group   = Group.objects.get(name="Agent simple")
            agents  = User.objects.filter(groups=group).order_by('username')
            # Annoter avec les permissions existantes
            perms_map = {
                p.user_id: p
                for p in AgentPermission.objects.filter(user__in=agents)
            }
            ctx['agents']     = agents
            ctx['perms_map']  = perms_map
        except Group.DoesNotExist:
            ctx['agents']    = []
            ctx['perms_map'] = {}
        return ctx


class AgentPermissionsEditView(ChefServiceRequiredMixin, FrontendView):
    """Édition des permissions d'un agent simple."""
    template_name = 'v2/misc/gestion_agent_permissions.html'
    active_page   = 'gestion_agents'

    # Groupes de permissions pour l'affichage structuré
    PERM_GROUPS = [
        ("Catalogue des matières", [
            ("perm_categories",  "Catégories"),
            ("perm_matieres",    "Matières"),
            ("perm_comptes",     "Comptes d'imputation"),
        ]),
        ("Achats & Entrées", [
            ("perm_achats",    "Achats"),
            ("perm_dons",      "Dons"),
            ("perm_legs",      "Legs"),
            ("perm_dotations", "Dotations"),
        ]),
        ("Prêts & Retours", [
            ("perm_prets",                "Prêts accordés"),
            ("perm_retours_fournisseurs", "Retours fournisseurs"),
        ]),
        ("Stock", [
            ("perm_stock_courant", "Stock courant (par dépôt)"),
            ("perm_stock_actuel",  "Stock actuel (tous dépôts)"),
            ("perm_mouvements",    "Mouvements de stock"),
            ("perm_sorties_stock", "Sorties de stock"),
            ("perm_transferts",    "Transferts inter-dépôts"),
        ]),
        ("Sorties définitives", [
            ("perm_sorties_definitives", "Sorties définitives"),
            ("perm_reforme",             "Réforme"),
        ]),
        ("Référentiels", [
            ("perm_fournisseurs", "Fournisseurs"),
            ("perm_donateurs",    "Donateurs"),
            ("perm_depots",       "Dépôts / Sites"),
            ("perm_services",     "Services"),
            ("perm_unites",       "Unités de mesure"),
        ]),
        ("Registres", [
            ("perm_livre_journal", "Grand Journal"),
        ]),
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agent = get_object_or_404(User, pk=self.kwargs['pk'])
        perms, _ = AgentPermission.objects.get_or_create(user=agent)

        # Construire la structure avec valeurs actuelles
        perm_groups_values = []
        for group_label, fields in self.PERM_GROUPS:
            rows = [(key, label, getattr(perms, key)) for key, label in fields]
            perm_groups_values.append((group_label, rows))

        ctx['agent']        = agent
        ctx['perms']        = perms
        ctx['perm_groups']  = perm_groups_values
        return ctx

    def post(self, request, pk):
        agent = get_object_or_404(User, pk=pk)
        # Vérifier que l'agent est bien un Agent simple
        if not agent.groups.filter(name="Agent simple").exists():
            messages.error(request, "Cet utilisateur n'est pas un agent simple.")
            return redirect('frontend:gestion_agents')

        perms, _ = AgentPermission.objects.get_or_create(user=agent)
        all_keys = [key for _, fields in self.PERM_GROUPS for key, _ in fields]
        for key in all_keys:
            setattr(perms, key, key in request.POST)
        perms.save()
        logger.info(
            "Permissions de l'agent %s mises à jour par %s",
            agent.username, request.user.username
        )
        messages.success(request, f"Permissions de {agent.username} sauvegardées.")
        return redirect('frontend:gestion_agent_permissions', pk=pk)


class AgentCreateView(ChefServiceRequiredMixin, FrontendView):
    """Création d'un compte agent simple par le chef de service."""
    template_name = 'v2/misc/gestion_agent_create.html'
    active_page   = 'gestion_agents'

    def post(self, request):
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        errors = []
        if not username:
            errors.append("Le nom d'utilisateur est obligatoire.")
        if User.objects.filter(username=username).exists():
            errors.append(f"Le nom d'utilisateur « {username} » est déjà pris.")
        if not password:
            errors.append("Le mot de passe est obligatoire.")
        if password != password2:
            errors.append("Les mots de passe ne correspondent pas.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('frontend:gestion_agent_create')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        group, _ = Group.objects.get_or_create(name="Agent simple")
        user.groups.add(group)
        AgentPermission.objects.create(user=user)  # permissions par défaut
        logger.info("Agent %s créé par %s", username, request.user.username)
        messages.success(request, f"Compte agent « {username} » créé avec succès.")
        return redirect('frontend:gestion_agent_permissions', pk=user.pk)
