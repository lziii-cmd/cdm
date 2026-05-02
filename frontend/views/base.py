# frontend/views/base.py
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class FrontendView(LoginRequiredMixin, TemplateView):
    """
    Vue de base pour toutes les pages frontend.

    Attributs configurables sur les sous-classes :
      active_page      (str)  – identifiant de la page active pour la sidebar
      inventory_view   (bool) – True = vue inventaire, inaccessible au superadmin
      agent_perm_key   (str)  – clé AgentPermission à vérifier pour les agents simples
    """
    active_page    = 'dashboard'
    inventory_view = False
    agent_perm_key = None
    login_url      = '/app/login/'

    # ── dispatch : contrôle d'accès par rôle ──────────────────────────────────
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from urllib.parse import urlencode
            next_url = request.get_full_path()
            return redirect(f"{self.login_url}?{urlencode({'next': next_url})}")

        from core.roles import get_user_role, agent_has_perm, ROLE_SUPERADMIN, ROLE_AGENT

        role = get_user_role(request.user)

        # Le superadmin n'a pas accès aux vues inventaire
        if role == ROLE_SUPERADMIN and self.inventory_view:
            messages.warning(
                request,
                "L'administrateur système n'a pas accès à cette section."
            )
            return redirect('frontend:dashboard')

        # Vérification permission agent
        if role == ROLE_AGENT and self.agent_perm_key:
            if not agent_has_perm(request.user, self.agent_perm_key):
                messages.error(request, "Vous n'avez pas accès à cette section.")
                return redirect('frontend:dashboard')

        # Bypasse LoginRequiredMixin (déjà géré ci-dessus)
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

    # ── contexte commun ────────────────────────────────────────────────────────
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_page'] = self.active_page
        ctx['notif_count'] = self._get_notif_count()

        # Rôle et permissions dans le contexte template
        from core.roles import get_user_role, get_agent_perms, ROLE_SUPERADMIN, ROLE_CHEF_SERVICE, ROLE_AGENT
        role = get_user_role(self.request.user)
        ctx['user_role']        = role
        ctx['is_superadmin']    = role == ROLE_SUPERADMIN
        ctx['is_chef_service']  = role == ROLE_CHEF_SERVICE
        ctx['is_agent']         = role == ROLE_AGENT
        if role == ROLE_AGENT:
            ctx['agent_perms'] = get_agent_perms(self.request.user)
        else:
            ctx['agent_perms'] = None

        return ctx

    def _get_notif_count(self):
        try:
            from core.models import Notification
            return Notification.objects.filter(lue=False).count()
        except Exception:
            return 0
