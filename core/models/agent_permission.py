# core/models/agent_permission.py
import logging
from django.contrib.auth import get_user_model
from django.db import models

logger = logging.getLogger(__name__)
User = get_user_model()


class AgentPermission(models.Model):
    """Permissions granulaires pour un agent simple, configurées par le chef de service."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_permissions',
        verbose_name="Utilisateur",
    )

    # ── Catalogue des matières ──
    perm_categories           = models.BooleanField(default=True,  verbose_name="Catégories")
    perm_matieres             = models.BooleanField(default=True,  verbose_name="Matières")
    perm_comptes              = models.BooleanField(default=True,  verbose_name="Comptes d'imputation")

    # ── Achats & Entrées ──
    perm_achats               = models.BooleanField(default=True,  verbose_name="Achats")
    perm_dons                 = models.BooleanField(default=True,  verbose_name="Dons")
    perm_legs                 = models.BooleanField(default=True,  verbose_name="Legs")
    perm_dotations            = models.BooleanField(default=True,  verbose_name="Dotations")

    # ── Prêts & Retours ──
    perm_prets                = models.BooleanField(default=True,  verbose_name="Prêts accordés")
    perm_retours_fournisseurs = models.BooleanField(default=True,  verbose_name="Retours fournisseurs")

    # ── Stock ──
    perm_stock_courant        = models.BooleanField(default=True,  verbose_name="Stock courant (par dépôt)")
    perm_stock_actuel         = models.BooleanField(default=True,  verbose_name="Stock actuel (tous dépôts)")
    perm_mouvements           = models.BooleanField(default=True,  verbose_name="Mouvements de stock")
    perm_sorties_stock        = models.BooleanField(default=True,  verbose_name="Sorties de stock")
    perm_transferts           = models.BooleanField(default=False, verbose_name="Transferts inter-dépôts")

    # ── Sorties définitives ──
    perm_sorties_definitives  = models.BooleanField(default=True,  verbose_name="Sorties définitives")
    perm_reforme              = models.BooleanField(default=False, verbose_name="Réforme")

    # ── Référentiels ──
    perm_fournisseurs         = models.BooleanField(default=True,  verbose_name="Fournisseurs")
    perm_donateurs            = models.BooleanField(default=True,  verbose_name="Donateurs")
    perm_depots               = models.BooleanField(default=True,  verbose_name="Dépôts / Sites")
    perm_services             = models.BooleanField(default=True,  verbose_name="Services")
    perm_unites               = models.BooleanField(default=True,  verbose_name="Unités de mesure")

    # ── Registres ──
    perm_livre_journal        = models.BooleanField(default=True,  verbose_name="Grand Journal")

    class Meta:
        verbose_name = "Permissions agent"
        verbose_name_plural = "Permissions agents"
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"Permissions de {self.user.username}"

    def perm_fields(self):
        """Retourne la liste des (field_name, verbose_name, value) pour affichage."""
        result = []
        for f in self._meta.get_fields():
            if hasattr(f, 'verbose_name') and f.name.startswith('perm_'):
                result.append((f.name, f.verbose_name, getattr(self, f.name)))
        return result
