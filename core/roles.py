# core/roles.py
"""
Gestion des rôles utilisateurs ENSMG.

Trois rôles :
  - superadmin   : is_superuser=True — gestion système uniquement, zéro accès inventaire
  - chef_service : groupe "Chef de service" — accès complet inventaire + gestion agents
  - agent        : groupe "Agent simple" — accès filtré par AgentPermission
"""
import logging

logger = logging.getLogger(__name__)

ROLE_SUPERADMIN   = "superadmin"
ROLE_CHEF_SERVICE = "chef_service"
ROLE_AGENT        = "agent"
ROLE_UNKNOWN      = "unknown"

GROUP_CHEF_SERVICE = "Chef de service"
GROUP_AGENT        = "Agent simple"


def get_user_role(user):
    """Retourne le rôle de l'utilisateur connecté."""
    if not user or not user.is_authenticated:
        return ROLE_UNKNOWN
    if user.is_superuser:
        return ROLE_SUPERADMIN
    if user.groups.filter(name=GROUP_CHEF_SERVICE).exists():
        return ROLE_CHEF_SERVICE
    if user.groups.filter(name=GROUP_AGENT).exists():
        return ROLE_AGENT
    # Fallback pour les comptes is_staff sans groupe explicite
    if user.is_staff:
        return ROLE_CHEF_SERVICE
    return ROLE_AGENT


def is_superadmin(user):
    return get_user_role(user) == ROLE_SUPERADMIN


def is_chef_service(user):
    return get_user_role(user) == ROLE_CHEF_SERVICE


def is_agent(user):
    return get_user_role(user) == ROLE_AGENT


def get_agent_perms(user):
    """Retourne l'objet AgentPermission pour un agent, None si non existant."""
    from core.models.agent_permission import AgentPermission
    try:
        return AgentPermission.objects.select_related('user').get(user=user)
    except AgentPermission.DoesNotExist:
        return None
    except Exception:
        logger.exception("Erreur lors de la récupération des permissions agent pour %s", user)
        return None


def agent_has_perm(user, perm_key):
    """
    Vérifie si l'utilisateur a accès à un module donné.
    - superadmin / chef_service → toujours True (hors contrôle d'inventaire du superadmin)
    - agent → vérifie AgentPermission.perm_key
    - Si l'agent n'a pas d'AgentPermission configurée → accès accordé par défaut
    """
    role = get_user_role(user)
    if role in (ROLE_SUPERADMIN, ROLE_CHEF_SERVICE):
        return True
    perms = get_agent_perms(user)
    if perms is None:
        return True  # Pas de restriction configurée = accès accordé
    return bool(getattr(perms, perm_key, True))
