# Signals pour l'audit trail
import logging
from django.core.exceptions import ValidationError

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
        from django.contrib.auth.models import Group, User
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
