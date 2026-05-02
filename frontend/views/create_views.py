# frontend/views/create_views.py
"""
Vues de création pour les principaux documents d'entrée/sortie.
Chaque vue gère l'en-tête + les lignes dans un seul formulaire HTML dynamique.
"""
import logging
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import ValidationError

from django.utils import timezone
from .base import FrontendView

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Achat + LigneAchat
# ─────────────────────────────────────────────────────────────
class AchatCreateView(FrontendView):
    template_name = 'v2/achats/create.html'
    active_page   = 'achats'
    inventory_view = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.models import Fournisseur, Depot
        from catalog.models import Matiere
        ctx['fournisseurs'] = Fournisseur.objects.order_by('raison_sociale')
        ctx['depots']       = Depot.objects.filter(actif=True).order_by('nom')
        ctx['matieres']     = Matiere.objects.select_related('categorie').order_by('designation')
        ctx['today']        = timezone.now().date().isoformat()
        return ctx

    def post(self, request, *args, **kwargs):
        from purchasing.models import Achat, LigneAchat
        from core.models import Fournisseur, Depot
        from catalog.models import Matiere
        from decimal import Decimal, InvalidOperation

        data = request.POST

        # ── Validation en-tête ──
        errors = []
        fournisseur_id = data.get('fournisseur')
        date_achat     = data.get('date_achat')
        tva_active     = data.get('tva_active') == 'on'
        depot_id       = data.get('depot') or None
        numero_facture = data.get('numero_facture', '').strip()
        commentaire    = data.get('commentaire', '').strip()

        if not fournisseur_id:
            errors.append("Fournisseur obligatoire.")
        if not date_achat:
            errors.append("Date d'achat obligatoire.")

        # ── Lignes ──
        matieres_ids  = data.getlist('ligne_matiere')
        quantites     = data.getlist('ligne_quantite')
        prix_unitaires= data.getlist('ligne_pu')

        lignes_data = []
        for i, m_id in enumerate(matieres_ids):
            if not m_id:
                continue
            try:
                qte = Decimal(quantites[i].replace(',', '.') if i < len(quantites) else '0')
                pu  = Decimal(prix_unitaires[i].replace(',', '.') if i < len(prix_unitaires) else '0')
            except (InvalidOperation, IndexError):
                errors.append(f"Ligne {i+1} : quantité ou prix invalide.")
                continue
            if qte <= 0:
                errors.append(f"Ligne {i+1} : la quantité doit être > 0.")
                continue
            lignes_data.append({'matiere_id': m_id, 'quantite': qte, 'prix_unitaire': pu})

        if not lignes_data:
            errors.append("Au moins une ligne est requise.")

        if errors:
            for e in errors:
                messages.error(request, e)
            ctx = self.get_context_data()
            ctx['post_data'] = data
            return self.render_to_response(ctx)

        try:
            with transaction.atomic():
                achat = Achat(
                    fournisseur_id=fournisseur_id,
                    date_achat=date_achat,
                    tva_active=tva_active,
                    depot_id=depot_id,
                    numero_facture=numero_facture,
                    commentaire=commentaire,
                )
                achat.full_clean(exclude=['code', 'total_ht', 'total_tva', 'total_ttc'])
                achat.save()
                for l in lignes_data:
                    ligne = LigneAchat(
                        achat=achat,
                        matiere_id=l['matiere_id'],
                        quantite=l['quantite'],
                        prix_unitaire=l['prix_unitaire'],
                    )
                    ligne.full_clean(exclude=['total_ligne_ht'])
                    ligne.save()
                achat.recompute_totaux()
                Achat.objects.filter(pk=achat.pk).update(
                    total_ht=achat.total_ht,
                    total_tva=achat.total_tva,
                    total_ttc=achat.total_ttc,
                )
            messages.success(request, f"Achat {achat.code} créé avec succès.")
            return redirect('frontend:achat_detail', pk=achat.pk)
        except ValidationError as exc:
            for field, errs in (exc.message_dict.items() if hasattr(exc, 'message_dict') else {'__all__': exc.messages}.items()):
                for e in errs:
                    messages.error(request, e)
        except Exception:
            logger.exception("Erreur lors de la création d'un achat")
            messages.error(request, "Erreur inattendue lors de la création.")

        ctx = self.get_context_data()
        ctx['post_data'] = data
        return self.render_to_response(ctx)


# ─────────────────────────────────────────────────────────────
# Don + LigneDon
# ─────────────────────────────────────────────────────────────
class DonCreateView(FrontendView):
    template_name  = 'v2/dons/create.html'
    active_page    = 'dons'
    inventory_view = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.models import Donateur, Depot
        from catalog.models import Matiere
        ctx['donateurs'] = Donateur.objects.order_by('raison_sociale')
        ctx['depots']    = Depot.objects.filter(actif=True).order_by('nom')
        ctx['matieres']  = Matiere.objects.select_related('categorie').order_by('designation')
        ctx['today']     = timezone.now().date().isoformat()
        return ctx

    def post(self, request, *args, **kwargs):
        from purchasing.models import Don
        from purchasing.models.don import LigneDon
        from decimal import Decimal, InvalidOperation
        from django.utils import timezone

        data = request.POST
        errors = []

        donateur_id  = data.get('donateur')
        date_don     = data.get('date_don')
        depot_id     = data.get('depot') or None
        numero_piece = data.get('numero_piece', '').strip()

        if not donateur_id:
            errors.append("Donateur obligatoire.")
        if not date_don:
            errors.append("Date du don obligatoire.")
        if not depot_id:
            errors.append("Dépôt de réception obligatoire.")

        matieres_ids  = data.getlist('ligne_matiere')
        quantites     = data.getlist('ligne_quantite')
        prix_unitaires= data.getlist('ligne_pu')

        lignes_data = []
        for i, m_id in enumerate(matieres_ids):
            if not m_id:
                continue
            try:
                qte = Decimal(quantites[i].replace(',', '.') if i < len(quantites) else '0')
                pu  = Decimal(prix_unitaires[i].replace(',', '.') if i < len(prix_unitaires) else '0')
            except (InvalidOperation, IndexError):
                errors.append(f"Ligne {i+1} : quantité ou prix invalide.")
                continue
            if qte <= 0:
                errors.append(f"Ligne {i+1} : la quantité doit être > 0.")
                continue
            lignes_data.append({'matiere_id': m_id, 'quantite': qte, 'prix_unitaire': pu})

        if not lignes_data:
            errors.append("Au moins une ligne est requise.")

        if errors:
            for e in errors:
                messages.error(request, e)
            ctx = self.get_context_data()
            ctx['post_data'] = data
            return self.render_to_response(ctx)

        try:
            with transaction.atomic():
                don = Don(
                    donateur_id=donateur_id,
                    date_don=date_don,
                    depot_id=depot_id,
                    numero_piece=numero_piece,
                )
                don.full_clean(exclude=['code', 'total_valeur'])
                don.save()
                for l in lignes_data:
                    ligne = LigneDon(
                        don=don,
                        matiere_id=l['matiere_id'],
                        quantite=l['quantite'],
                        prix_unitaire=l['prix_unitaire'],
                    )
                    ligne.full_clean(exclude=['total_ligne'])
                    ligne.save()
                don.recompute_total()
                Don.objects.filter(pk=don.pk).update(total_valeur=don.total_valeur)
            messages.success(request, f"Don {don.code} créé avec succès.")
            return redirect('frontend:don_detail', pk=don.pk)
        except ValidationError as exc:
            for field, errs in (exc.message_dict.items() if hasattr(exc, 'message_dict') else {'__all__': exc.messages}.items()):
                for e in errs:
                    messages.error(request, e)
        except Exception:
            logger.exception("Erreur lors de la création d'un don")
            messages.error(request, "Erreur inattendue lors de la création.")

        ctx = self.get_context_data()
        ctx['post_data'] = data
        return self.render_to_response(ctx)


# ─────────────────────────────────────────────────────────────
# Legs (ExternalStockEntry via LegsEntry)
# ─────────────────────────────────────────────────────────────
class LegsCreateView(FrontendView):
    template_name  = 'v2/legs/create.html'
    active_page    = 'legs'
    inventory_view = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.models import Depot
        from core.models.external_source import ExternalSource
        from catalog.models import Matiere
        ctx['sources']  = ExternalSource.objects.filter(source_type='LEGS').order_by('name')
        ctx['depots']   = Depot.objects.filter(actif=True).order_by('nom')
        ctx['matieres'] = Matiere.objects.select_related('categorie').order_by('designation')
        ctx['today']    = timezone.now().date().isoformat()
        return ctx

    def post(self, request, *args, **kwargs):
        from purchasing.models.legs_entry import LegsEntry
        from purchasing.models.external_stock_entry_line import ExternalStockEntryLine
        from decimal import Decimal, InvalidOperation

        data = request.POST
        errors = []

        source_id       = data.get('source')
        received_date   = data.get('received_date')
        depot_id        = data.get('depot') or None
        document_number = data.get('document_number', '').strip()
        comment         = data.get('comment', '').strip()

        if not source_id:
            errors.append("Source obligatoire.")
        if not received_date:
            errors.append("Date de réception obligatoire.")
        if not depot_id:
            errors.append("Dépôt de réception obligatoire.")

        matieres_ids  = data.getlist('ligne_matiere')
        quantites     = data.getlist('ligne_quantite')
        prix_unitaires= data.getlist('ligne_pu')

        lignes_data = []
        for i, m_id in enumerate(matieres_ids):
            if not m_id:
                continue
            try:
                qte = Decimal(quantites[i].replace(',', '.') if i < len(quantites) else '0')
                pu  = Decimal(prix_unitaires[i].replace(',', '.') if i < len(prix_unitaires) else '0')
            except (InvalidOperation, IndexError):
                errors.append(f"Ligne {i+1} : quantité invalide.")
                continue
            if qte <= 0:
                errors.append(f"Ligne {i+1} : la quantité doit être > 0.")
                continue
            lignes_data.append({'matiere_id': m_id, 'quantite': qte, 'unit_price': pu})

        if not lignes_data:
            errors.append("Au moins une ligne est requise.")

        if errors:
            for e in errors:
                messages.error(request, e)
            ctx = self.get_context_data()
            ctx['post_data'] = data
            return self.render_to_response(ctx)

        try:
            with transaction.atomic():
                entry = LegsEntry(
                    source_id=source_id,
                    received_date=received_date,
                    depot_id=depot_id,
                    document_number=document_number,
                    comment=comment,
                )
                entry.full_clean(exclude=['code', 'total_value'])
                entry.save()
                for l in lignes_data:
                    ligne = ExternalStockEntryLine(
                        entry=entry,
                        matiere_id=l['matiere_id'],
                        quantity=l['quantite'],
                        unit_price=l['unit_price'],
                    )
                    ligne.full_clean(exclude=['total_line'])
                    ligne.save()
                entry.recompute_totals()
            messages.success(request, f"Legs {entry.code} créé avec succès.")
            return redirect('frontend:legs_detail', pk=entry.pk)
        except ValidationError as exc:
            for field, errs in (exc.message_dict.items() if hasattr(exc, 'message_dict') else {'__all__': exc.messages}.items()):
                for e in errs:
                    messages.error(request, e)
        except Exception:
            logger.exception("Erreur lors de la création d'un legs")
            messages.error(request, "Erreur inattendue lors de la création.")

        ctx = self.get_context_data()
        ctx['post_data'] = data
        return self.render_to_response(ctx)


# ─────────────────────────────────────────────────────────────
# Prêt + LignePret
# ─────────────────────────────────────────────────────────────
class PretCreateView(FrontendView):
    template_name  = 'v2/prets/create.html'
    active_page    = 'prets'
    inventory_view = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.models import Service, Depot
        from catalog.models import Matiere
        ctx['services'] = Service.objects.filter(actif=True).order_by('libelle')
        ctx['depots']   = Depot.objects.filter(actif=True).order_by('nom')
        ctx['matieres'] = Matiere.objects.select_related('categorie').order_by('designation')
        ctx['today']    = timezone.now().date().isoformat()
        return ctx

    def post(self, request, *args, **kwargs):
        from purchasing.models import Pret
        from purchasing.models.pret import LignePret
        from decimal import Decimal, InvalidOperation

        data = request.POST
        errors = []

        service_id  = data.get('service')
        date_pret   = data.get('date_pret')
        depot_id    = data.get('depot') or None
        commentaire = data.get('commentaire', '').strip()

        if not service_id:
            errors.append("Service bénéficiaire obligatoire.")
        if not date_pret:
            errors.append("Date de prêt obligatoire.")
        if not depot_id:
            errors.append("Dépôt source obligatoire.")

        matieres_ids = data.getlist('ligne_matiere')
        quantites    = data.getlist('ligne_quantite')

        lignes_data = []
        for i, m_id in enumerate(matieres_ids):
            if not m_id:
                continue
            try:
                qte = Decimal(quantites[i].replace(',', '.') if i < len(quantites) else '0')
            except (InvalidOperation, IndexError):
                errors.append(f"Ligne {i+1} : quantité invalide.")
                continue
            if qte <= 0:
                errors.append(f"Ligne {i+1} : la quantité doit être > 0.")
                continue
            lignes_data.append({'matiere_id': m_id, 'quantite': qte})

        if not lignes_data:
            errors.append("Au moins une ligne est requise.")

        if errors:
            for e in errors:
                messages.error(request, e)
            ctx = self.get_context_data()
            ctx['post_data'] = data
            return self.render_to_response(ctx)

        try:
            with transaction.atomic():
                pret = Pret(
                    service_id=service_id,
                    date_pret=date_pret,
                    depot_id=depot_id,
                    commentaire=commentaire,
                )
                pret.full_clean(exclude=['code', 'est_clos'])
                pret.save()
                for l in lignes_data:
                    ligne = LignePret(
                        pret=pret,
                        matiere_id=l['matiere_id'],
                        quantite=l['quantite'],
                    )
                    ligne.full_clean(exclude=[])
                    ligne.save()
            messages.success(request, f"Prêt {pret.code} créé avec succès.")
            return redirect('frontend:pret_detail', pk=pret.pk)
        except ValidationError as exc:
            for field, errs in (exc.message_dict.items() if hasattr(exc, 'message_dict') else {'__all__': exc.messages}.items()):
                for e in errs:
                    messages.error(request, e)
        except Exception:
            logger.exception("Erreur lors de la création d'un prêt")
            messages.error(request, "Erreur inattendue lors de la création.")

        ctx = self.get_context_data()
        ctx['post_data'] = data
        return self.render_to_response(ctx)
