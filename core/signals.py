# core/signals.py
import logging
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def un_seul_chef_de_service(sender, action, instance, pk_set, **kwargs):
    """
    Garantit qu'un seul utilisateur peut appartenir au groupe "Chef de service".
    Bloque l'ajout si le groupe contient déjà un autre membre.
    Connecté manuellement dans CoreConfig.ready() après que les modèles sont prêts.
    """
    if action != 'pre_add' or not pk_set:
        return
    try:
        from django.contrib.auth.models import Group
        chef_group = Group.objects.filter(name='Chef de service').first()
        if chef_group is None or chef_group.pk not in pk_set:
            return
        already = User.objects.filter(groups=chef_group).exclude(pk=instance.pk)
        if already.exists():
            existing = already.first()
            raise ValidationError(
                f"Un seul Chef de service est autorisé. "
                f"'{existing.username}' occupe déjà ce rôle."
            )
    except ValidationError:
        raise
    except Exception:
        logger.error("Erreur dans le signal m2m_changed Chef de service", exc_info=True)

# Les signaux core (ex : création automatique de notifications sur événements métier)
# sont à ajouter ici. Chaque signal doit loguer les erreurs sans les avaler :
#
# @receiver(post_save, sender=MonModele)
# def mon_signal(sender, instance, created, **kwargs):
#     try:
#         ...
#     except Exception:
#         logger.error("Erreur dans le signal post_save de MonModele", exc_info=True)
