# core/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Les signaux core (ex : création automatique de notifications sur événements métier)
# sont à ajouter ici. Chaque signal doit loguer les erreurs sans les avaler :
#
# @receiver(post_save, sender=MonModele)
# def mon_signal(sender, instance, created, **kwargs):
#     try:
#         ...
#     except Exception:
#         logger.error("Erreur dans le signal post_save de MonModele", exc_info=True)
