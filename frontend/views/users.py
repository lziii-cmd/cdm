# frontend/views/users.py
"""
Gestion des utilisateurs — réservé au Super Administrateur.
Remplace complètement l'interface /admin/auth/user/.
"""
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect

from core.roles import get_user_role, is_superadmin
from .base import FrontendView

logger = logging.getLogger(__name__)
User = get_user_model()

ROLE_LABELS = {
    'superadmin':   'Super Administrateur',
    'chef_service': 'Chef de service',
    'agent':        'Agent simple',
    'unknown':      'Inconnu',
}


class SuperadminRequiredMixin:
    """Restreint la vue au Super Administrateur uniquement."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/admin/login/')
        if not is_superadmin(request.user):
            messages.error(request, "Cette section est réservée au Super Administrateur.")
            return redirect('frontend:dashboard')
        return super().dispatch(request, *args, **kwargs)


# ── Liste ──────────────────────────────────────────────────────────────────────

class UserListView(SuperadminRequiredMixin, FrontendView):
    template_name = 'v2/misc/users.html'
    active_page   = 'users'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        users = User.objects.prefetch_related('groups').order_by('username')
        ctx['users_list'] = [
            {
                'user':       u,
                'role':       get_user_role(u),
                'role_label': ROLE_LABELS.get(get_user_role(u), 'Inconnu'),
            }
            for u in users
        ]
        return ctx


# ── Création ───────────────────────────────────────────────────────────────────

class UserCreateView(SuperadminRequiredMixin, FrontendView):
    template_name = 'v2/misc/user_create.html'
    active_page   = 'users'

    def post(self, request, *args, **kwargs):
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role      = request.POST.get('role', 'agent')

        if not username or not password:
            messages.error(request, "Le nom d'utilisateur et le mot de passe sont obligatoires.")
            return redirect('frontend:user_create')

        if password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('frontend:user_create')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Le nom d'utilisateur « {username} » est déjà pris.")
            return redirect('frontend:user_create')

        try:
            if role == 'superadmin':
                user = User.objects.create_superuser(
                    username=username, email=email, password=password
                )
            elif role == 'chef_service':
                user = User.objects.create_user(
                    username=username, email=email, password=password, is_staff=True
                )
                groupe, _ = Group.objects.get_or_create(name='Chef de service')
                user.groups.add(groupe)
            else:
                user = User.objects.create_user(
                    username=username, email=email, password=password, is_staff=False
                )
                groupe, _ = Group.objects.get_or_create(name='Agent simple')
                user.groups.add(groupe)

            messages.success(request, f"Compte « {username} » créé avec succès.")
            logger.info("Utilisateur %s créé par %s (rôle: %s)", username, request.user.username, role)
        except Exception:
            logger.exception("Erreur lors de la création de l'utilisateur %s", username)
            messages.error(request, "Une erreur est survenue lors de la création du compte.")

        return redirect('frontend:users')


# ── Modification ───────────────────────────────────────────────────────────────

class UserEditView(SuperadminRequiredMixin, FrontendView):
    template_name = 'v2/misc/user_edit.html'
    active_page   = 'users'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        edited = get_object_or_404(User, pk=self.kwargs['pk'])
        ctx['edited_user']      = edited
        ctx['edited_user_role'] = get_user_role(edited)
        ctx['role_labels']      = ROLE_LABELS
        return ctx

    def post(self, request, *args, **kwargs):
        edited    = get_object_or_404(User, pk=self.kwargs['pk'])
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        role      = request.POST.get('role', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if password and password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('frontend:user_edit', pk=edited.pk)

        try:
            edited.email     = email
            edited.is_active = is_active

            if password:
                edited.set_password(password)

            # Mise à jour du rôle si changé
            current_role = get_user_role(edited)
            if role and role != current_role:
                edited.groups.clear()
                edited.is_superuser = False
                edited.is_staff     = False
                if role == 'superadmin':
                    edited.is_superuser = True
                    edited.is_staff     = True
                elif role == 'chef_service':
                    edited.is_staff = True
                    groupe, _ = Group.objects.get_or_create(name='Chef de service')
                    edited.groups.add(groupe)
                else:
                    groupe, _ = Group.objects.get_or_create(name='Agent simple')
                    edited.groups.add(groupe)

            edited.save()
            messages.success(request, f"Compte « {edited.username} » mis à jour.")
            logger.info(
                "Utilisateur %s modifié par %s (rôle: %s→%s)",
                edited.username, request.user.username, current_role, role or current_role
            )
        except Exception:
            logger.exception("Erreur lors de la mise à jour de l'utilisateur %s", edited.username)
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:users')


# ── Suppression ────────────────────────────────────────────────────────────────

class UserDeleteView(SuperadminRequiredMixin, FrontendView):
    template_name = 'v2/misc/user_confirm_delete.html'
    active_page   = 'users'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['edited_user'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        edited = get_object_or_404(User, pk=self.kwargs['pk'])

        if edited.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('frontend:users')

        username = edited.username
        try:
            edited.delete()
            messages.success(request, f"Compte « {username} » supprimé.")
            logger.info("Utilisateur %s supprimé par %s", username, request.user.username)
        except Exception:
            logger.exception("Erreur lors de la suppression de l'utilisateur %s", username)
            messages.error(request, "Une erreur est survenue lors de la suppression.")

        return redirect('frontend:users')
