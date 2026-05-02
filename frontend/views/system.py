# frontend/views/system.py
import logging
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect, render
from django.views import View
from .base import FrontendView
from core.roles import is_superadmin, is_chef_service

logger = logging.getLogger(__name__)


class LoginView(View):
    """Page de connexion frontend — remplace /admin/login/."""
    template_name = 'v2/misc/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        return render(request, self.template_name, {
            'next': request.GET.get('next', '/app/')
        })

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/app/')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            logger.info("Connexion réussie : %s", username)
            return redirect(next_url if next_url.startswith('/') else '/app/')
        else:
            # Distinguer compte désactivé de mauvais identifiants
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            try:
                existing = UserModel.objects.get(username=username)
                if not existing.is_active:
                    messages.error(request, "Ce compte est désactivé.")
                else:
                    messages.error(request, "Identifiant ou mot de passe incorrect.")
            except UserModel.DoesNotExist:
                messages.error(request, "Identifiant ou mot de passe incorrect.")
        return render(request, self.template_name, {
            'username': username,
            'next': next_url,
        })


class LogoutView(View):
    """Déconnexion — POST uniquement (protection CSRF)."""

    def post(self, request):
        auth.logout(request)
        return redirect('/')

    def get(self, request):
        # Sécurité : le GET redirige sans déconnecter
        return redirect('frontend:dashboard')


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
