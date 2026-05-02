# frontend/views/referentiels.py
import logging
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from .base import FrontendView
from core.roles import is_superadmin, is_chef_service

logger = logging.getLogger(__name__)


class ChefServiceRequiredMixin:
    """Restreint la vue au Chef de service ou au Super Administrateur."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from urllib.parse import urlencode
            return redirect(f"/app/login/?{urlencode({'next': request.get_full_path()})}")
        if not (is_superadmin(request.user) or is_chef_service(request.user)):
            messages.error(request, "Cette action est réservée au Chef de service ou à l'administrateur.")
            return redirect('frontend:dashboard')
        return super().dispatch(request, *args, **kwargs)


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


# ═══════════════════════════════════════════════════════════════
# FOURNISSEUR — CRUD
# ═══════════════════════════════════════════════════════════════

class FournisseurCreateView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/fournisseur_form.html'
    active_page = 'fournisseurs'

    def post(self, request, *args, **kwargs):
        from core.models import Fournisseur
        raison_sociale = request.POST.get('raison_sociale', '').strip()
        adresse        = request.POST.get('adresse', '').strip()
        numero         = request.POST.get('numero', '').strip()
        courriel       = request.POST.get('courriel', '').strip()
        ninea          = request.POST.get('ninea', '').strip() or None
        code_prefix    = request.POST.get('code_prefix', '').strip()

        if not raison_sociale:
            messages.error(request, "La raison sociale est obligatoire.")
            return redirect('frontend:fournisseur_create')

        if ninea and Fournisseur.objects.filter(ninea=ninea).exists():
            messages.error(request, f"Le NINEA « {ninea} » est déjà attribué à un autre fournisseur.")
            return redirect('frontend:fournisseur_create')

        try:
            f = Fournisseur.objects.create(
                raison_sociale=raison_sociale,
                adresse=adresse, numero=numero,
                courriel=courriel, ninea=ninea,
                code_prefix=code_prefix,
            )
            messages.success(request, f"Fournisseur « {f.raison_sociale} » créé.")
            logger.info("Fournisseur %s créé par %s", f.identifiant, request.user.username)
        except Exception:
            logger.exception("Erreur création fournisseur")
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:fournisseurs')


class FournisseurEditView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/fournisseur_form.html'
    active_page = 'fournisseurs'

    def get_context_data(self, **kwargs):
        from core.models import Fournisseur
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Fournisseur, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Fournisseur
        f = get_object_or_404(Fournisseur, pk=kwargs['pk'])
        raison_sociale = request.POST.get('raison_sociale', '').strip()
        adresse        = request.POST.get('adresse', '').strip()
        numero         = request.POST.get('numero', '').strip()
        courriel       = request.POST.get('courriel', '').strip()
        ninea          = request.POST.get('ninea', '').strip() or None
        code_prefix    = request.POST.get('code_prefix', '').strip()

        if not raison_sociale:
            messages.error(request, "La raison sociale est obligatoire.")
            return redirect('frontend:fournisseur_edit', pk=f.pk)

        if ninea and Fournisseur.objects.filter(ninea=ninea).exclude(pk=f.pk).exists():
            messages.error(request, f"Le NINEA « {ninea} » est déjà attribué à un autre fournisseur.")
            return redirect('frontend:fournisseur_edit', pk=f.pk)

        try:
            f.raison_sociale = raison_sociale
            f.adresse = adresse
            f.numero = numero
            f.courriel = courriel
            f.ninea = ninea
            if code_prefix:
                f.code_prefix = code_prefix
            f.save()
            messages.success(request, f"Fournisseur « {f.raison_sociale} » mis à jour.")
            logger.info("Fournisseur %s modifié par %s", f.identifiant, request.user.username)
        except Exception:
            logger.exception("Erreur modification fournisseur %s", f.pk)
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:fournisseurs')


class FournisseurDeleteView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/fournisseur_delete.html'
    active_page = 'fournisseurs'

    def get_context_data(self, **kwargs):
        from core.models import Fournisseur
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Fournisseur, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Fournisseur
        f = get_object_or_404(Fournisseur, pk=kwargs['pk'])
        nom = f.raison_sociale
        try:
            f.delete()
            messages.success(request, f"Fournisseur « {nom} » supprimé.")
            logger.info("Fournisseur %s supprimé par %s", nom, request.user.username)
        except Exception:
            logger.exception("Erreur suppression fournisseur %s", f.pk)
            messages.error(request, "Impossible de supprimer ce fournisseur (probablement référencé dans des achats).")

        return redirect('frontend:fournisseurs')


# ═══════════════════════════════════════════════════════════════
# DONATEUR — CRUD
# ═══════════════════════════════════════════════════════════════

class DonateurCreateView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/donateur_form.html'
    active_page = 'donateurs'

    def post(self, request, *args, **kwargs):
        from core.models import Donateur
        raison_sociale = request.POST.get('raison_sociale', '').strip()
        adresse        = request.POST.get('adresse', '').strip()
        telephone      = request.POST.get('telephone', '').strip()
        courriel       = request.POST.get('courriel', '').strip()
        remarque       = request.POST.get('remarque', '').strip()

        if not raison_sociale:
            messages.error(request, "La raison sociale est obligatoire.")
            return redirect('frontend:donateur_create')

        try:
            d = Donateur.objects.create(
                raison_sociale=raison_sociale,
                adresse=adresse, telephone=telephone,
                courriel=courriel, remarque=remarque,
            )
            messages.success(request, f"Donateur « {d.raison_sociale} » créé.")
            logger.info("Donateur %s créé par %s", d.identifiant, request.user.username)
        except Exception:
            logger.exception("Erreur création donateur")
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:donateurs')


class DonateurEditView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/donateur_form.html'
    active_page = 'donateurs'

    def get_context_data(self, **kwargs):
        from core.models import Donateur
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Donateur, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Donateur
        d = get_object_or_404(Donateur, pk=kwargs['pk'])
        raison_sociale = request.POST.get('raison_sociale', '').strip()
        adresse        = request.POST.get('adresse', '').strip()
        telephone      = request.POST.get('telephone', '').strip()
        courriel       = request.POST.get('courriel', '').strip()
        remarque       = request.POST.get('remarque', '').strip()

        if not raison_sociale:
            messages.error(request, "La raison sociale est obligatoire.")
            return redirect('frontend:donateur_edit', pk=d.pk)

        try:
            d.raison_sociale = raison_sociale
            d.adresse = adresse
            d.telephone = telephone
            d.courriel = courriel
            d.remarque = remarque
            d.save()
            messages.success(request, f"Donateur « {d.raison_sociale} » mis à jour.")
            logger.info("Donateur %s modifié par %s", d.identifiant, request.user.username)
        except Exception:
            logger.exception("Erreur modification donateur %s", d.pk)
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:donateurs')


class DonateurDeleteView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/donateur_delete.html'
    active_page = 'donateurs'

    def get_context_data(self, **kwargs):
        from core.models import Donateur
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Donateur, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Donateur
        d = get_object_or_404(Donateur, pk=kwargs['pk'])
        nom = d.raison_sociale
        try:
            d.delete()
            messages.success(request, f"Donateur « {nom} » supprimé.")
            logger.info("Donateur %s supprimé par %s", nom, request.user.username)
        except Exception:
            logger.exception("Erreur suppression donateur %s", d.pk)
            messages.error(request, "Impossible de supprimer ce donateur (probablement référencé dans des dons).")

        return redirect('frontend:donateurs')


# ═══════════════════════════════════════════════════════════════
# SERVICE — CRUD
# ═══════════════════════════════════════════════════════════════

class ServiceCreateView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/service_form.html'
    active_page = 'services'

    def post(self, request, *args, **kwargs):
        from core.models import Service
        code        = request.POST.get('code', '').strip().upper()
        libelle     = request.POST.get('libelle', '').strip()
        responsable = request.POST.get('responsable', '').strip()

        if not code or not libelle or not responsable:
            messages.error(request, "Le code, le libellé et le responsable sont obligatoires.")
            return redirect('frontend:service_create')

        if Service.objects.filter(code=code).exists():
            messages.error(request, f"Le code « {code} » est déjà utilisé.")
            return redirect('frontend:service_create')

        try:
            s = Service.objects.create(code=code, libelle=libelle, responsable=responsable)
            messages.success(request, f"Service « {s.libelle} » créé.")
            logger.info("Service %s créé par %s", s.code, request.user.username)
        except Exception:
            logger.exception("Erreur création service")
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:services')


class ServiceEditView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/service_form.html'
    active_page = 'services'

    def get_context_data(self, **kwargs):
        from core.models import Service
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Service, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Service
        s = get_object_or_404(Service, pk=kwargs['pk'])
        code        = request.POST.get('code', '').strip().upper()
        libelle     = request.POST.get('libelle', '').strip()
        responsable = request.POST.get('responsable', '').strip()
        actif       = request.POST.get('actif') == 'on'

        if not code or not libelle or not responsable:
            messages.error(request, "Le code, le libellé et le responsable sont obligatoires.")
            return redirect('frontend:service_edit', pk=s.pk)

        if Service.objects.filter(code=code).exclude(pk=s.pk).exists():
            messages.error(request, f"Le code « {code} » est déjà utilisé.")
            return redirect('frontend:service_edit', pk=s.pk)

        try:
            s.code = code
            s.libelle = libelle
            s.responsable = responsable
            s.actif = actif
            s.save()
            messages.success(request, f"Service « {s.libelle} » mis à jour.")
            logger.info("Service %s modifié par %s", s.code, request.user.username)
        except Exception:
            logger.exception("Erreur modification service %s", s.pk)
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:services')


class ServiceDeleteView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/service_delete.html'
    active_page = 'services'

    def get_context_data(self, **kwargs):
        from core.models import Service
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Service, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Service
        s = get_object_or_404(Service, pk=kwargs['pk'])
        nom = s.libelle
        try:
            s.delete()
            messages.success(request, f"Service « {nom} » supprimé.")
            logger.info("Service %s supprimé par %s", nom, request.user.username)
        except Exception:
            logger.exception("Erreur suppression service %s", s.pk)
            messages.error(request, "Impossible de supprimer ce service (référencé par des bureaux ou utilisateurs).")

        return redirect('frontend:services')


# ═══════════════════════════════════════════════════════════════
# DEPOT — CRUD
# ═══════════════════════════════════════════════════════════════

class DepotCreateView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/depot_form.html'
    active_page = 'depots'

    def get_context_data(self, **kwargs):
        from core.models import Service
        ctx = super().get_context_data(**kwargs)
        ctx['services_list'] = Service.objects.filter(actif=True).order_by('code')
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Depot, Service
        identifiant  = request.POST.get('identifiant', '').strip()
        nom          = request.POST.get('nom', '').strip()
        type_lieu    = request.POST.get('type_lieu', 'DEPOT').strip()
        service_id   = request.POST.get('service') or None
        localisation = request.POST.get('localisation', '').strip()

        if not identifiant or not nom:
            messages.error(request, "L'identifiant et le nom sont obligatoires.")
            return redirect('frontend:depot_create')

        try:
            service = Service.objects.get(pk=service_id) if service_id else None
            d = Depot(
                identifiant=identifiant, nom=nom,
                type_lieu=type_lieu, service=service,
                localisation=localisation,
            )
            d.full_clean()
            d.save()
            messages.success(request, f"Dépôt/Bureau « {d.nom} » créé.")
            logger.info("Depot %s créé par %s", d.identifiant, request.user.username)
        except ValidationError as e:
            for field, errs in e.message_dict.items() if hasattr(e, 'message_dict') else [('__all__', e.messages)]:
                for err in errs:
                    messages.error(request, err)
            return redirect('frontend:depot_create')
        except Exception:
            logger.exception("Erreur création depot")
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:depots')


class DepotEditView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/depot_form.html'
    active_page = 'depots'

    def get_context_data(self, **kwargs):
        from core.models import Depot, Service
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Depot, pk=self.kwargs['pk'])
        ctx['services_list'] = Service.objects.filter(actif=True).order_by('code')
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Depot, Service
        d = get_object_or_404(Depot, pk=kwargs['pk'])
        nom          = request.POST.get('nom', '').strip()
        type_lieu    = request.POST.get('type_lieu', 'DEPOT').strip()
        service_id   = request.POST.get('service') or None
        localisation = request.POST.get('localisation', '').strip()
        actif        = request.POST.get('actif') == 'on'

        if not nom:
            messages.error(request, "Le nom est obligatoire.")
            return redirect('frontend:depot_edit', pk=d.pk)

        try:
            service = Service.objects.get(pk=service_id) if service_id else None
            d.nom = nom
            d.type_lieu = type_lieu
            d.service = service
            d.localisation = localisation
            d.actif = actif
            d.full_clean()
            d.save()
            messages.success(request, f"Dépôt/Bureau « {d.nom} » mis à jour.")
            logger.info("Depot %s modifié par %s", d.identifiant, request.user.username)
        except ValidationError as e:
            for field, errs in e.message_dict.items() if hasattr(e, 'message_dict') else [('__all__', e.messages)]:
                for err in errs:
                    messages.error(request, err)
            return redirect('frontend:depot_edit', pk=d.pk)
        except Exception:
            logger.exception("Erreur modification depot %s", d.pk)
            messages.error(request, "Une erreur est survenue.")

        return redirect('frontend:depots')


class DepotDeleteView(ChefServiceRequiredMixin, FrontendView):
    template_name = 'v2/misc/depot_delete.html'
    active_page = 'depots'

    def get_context_data(self, **kwargs):
        from core.models import Depot
        ctx = super().get_context_data(**kwargs)
        ctx['instance'] = get_object_or_404(Depot, pk=self.kwargs['pk'])
        return ctx

    def post(self, request, *args, **kwargs):
        from core.models import Depot
        d = get_object_or_404(Depot, pk=kwargs['pk'])
        nom = d.nom
        try:
            d.delete()
            messages.success(request, f"Dépôt/Bureau « {nom} » supprimé.")
            logger.info("Depot %s supprimé par %s", nom, request.user.username)
        except Exception:
            logger.exception("Erreur suppression depot %s", d.pk)
            messages.error(request, "Impossible de supprimer ce lieu (du stock y est probablement affecté).")

        return redirect('frontend:depots')
