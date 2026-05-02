# catalog/signals.py
import logging

logger = logging.getLogger(__name__)

# Les signaux catalog (ex : invalidation de cache sur modification d'une matière)
# sont à ajouter ici. Chaque signal doit loguer les erreurs sans les avaler :
#
# @receiver(post_save, sender=Matiere)
# def on_matiere_save(sender, instance, created, **kwargs):
#     try:
#         ...
#     except Exception:
#         logger.error("Erreur dans le signal post_save de Matiere", exc_info=True)
