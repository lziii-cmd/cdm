# frontend/views/system.py
from django.contrib import messages
from django.shortcuts import redirect
from .base import FrontendView
from core.roles import is_superadmin, is_chef_service


class ExercicesListView(FrontendView):
    template_name = 'v2/misc/exercices.html'
    active_page = 'exercices'
    inventory_view = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from core.models import Exercice
            ctx['exercices'] = Exercice.objects.order_by('-annee')
        except Exception:
            ctx['exercices'] = []
        return ctx


class LivreJournalView(FrontendView):
    template_name = 'v2/misc/livre_journal.html'
    active_page = 'livre_journal'
    inventory_view = True
    agent_perm_key = 'perm_livre_journal'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from inventory.models import MouvementStock
            from django.core.paginator import Paginator
            qs = MouvementStock.objects.select_related(
                'matiere', 'depot', 'exercice'
            ).order_by('-date', '-id')
            paginator = Paginator(qs, 30)
            page_obj = paginator.get_page(self.request.GET.get('page', 1))
            ctx['page_obj'] = page_obj
            ctx['mouvements'] = page_obj.object_list
        except Exception:
            ctx['mouvements'] = []
        return ctx


class NotificationsView(FrontendView):
    template_name = 'v2/misc/notifications.html'
    active_page = 'notifications'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from core.models import Notification
            ctx['notifications'] = Notification.objects.order_by('-date_creation')[:50]
        except Exception:
            ctx['notifications'] = []
        return ctx


class ProfilView(FrontendView):
    template_name = 'v2/misc/profil.html'
    active_page = 'profil'

    def post(self, request, *args, **kwargs):
        """Changement de mot de passe depuis la page profil."""
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        if not password:
            messages.error(request, "Le mot de passe ne peut pas être vide.")
        elif password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif len(password) < 6:
            messages.error(request, "Le mot de passe doit contenir au moins 6 caractères.")
        else:
            request.user.set_password(password)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, "Mot de passe modifié avec succès.")
        return redirect('frontend:profil')


class SettingsView(FrontendView):
    template_name = 'v2/misc/settings.html'
    active_page = 'settings'

    def dispatch(self, request, *args, **kwargs):
        if not is_superadmin(request.user) and not is_chef_service(request.user):
            messages.error(request, "Accès refusé. Cette page est réservée aux administrateurs.")
            return redirect('frontend:dashboard')
        return super().dispatch(request, *args, **kwargs)
