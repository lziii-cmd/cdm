# MEMORY.md — Mémoire du projet ENSMG Comptabilité des Matières

Dernière mise à jour : 02/05/2026

## CONTEXTE ACTUEL
- Où on en est : Interface frontend v2 opérationnelle. Système de rôles complet. Gestion utilisateurs en frontend. 0 dépendance au Django admin depuis le frontend.
- Dernière fonctionnalité travaillée : Suppression totale des liens /admin/ dans les templates v2 + frontend
- Prochaine fonctionnalité prévue : Logout + dropdown profil topbar + sélecteur d'exercices interactif
- Problèmes ouverts : Pas de bouton logout accessible depuis le frontend

## DÉCISIONS TECHNIQUES
| Date | Décision | Pourquoi | Alternative écartée |
|------|----------|----------|---------------------|
| 02/05/2026 | Système de rôles via Django Groups + is_superuser | Flexible, natif Django, pas de modèle supplémentaire | Modèle Role custom |
| 02/05/2026 | FrontendView comme classe de base avec inventory_view et agent_perm_key | Contrôle d'accès centralisé, DRY | Décorateurs sur chaque vue |
| 02/05/2026 | Gestion utilisateurs dans /app/users/ (pas dans /admin/) | 0 dépendance admin pour les utilisateurs finaux | Django admin auth |
| 02/05/2026 | Changement de mot de passe inline sur /app/profil/ avec POST | Pas de dépendance admin, UX simple | /admin/password_change/ |

## CE QUI A ÉTÉ FAIT
| Date | Fonctionnalité | Statut | Notes |
|------|----------------|--------|-------|
| 02/05/2026 | Système de rôles (superadmin/chef_service/agent) | stable | core/roles.py |
| 02/05/2026 | Sidebar conditionnelle par rôle | stable | templates/v2/base.html |
| 02/05/2026 | Dashboard splitté par rôle | stable | dashboard.html + views/dashboard.py |
| 02/05/2026 | AgentPermission (22 permissions booléennes) | stable | Géré par chef de service |
| 02/05/2026 | CRUD utilisateurs frontend /app/users/ | stable | SuperadminRequiredMixin |
| 02/05/2026 | Changement de mot de passe sur /app/profil/ | stable | ProfilView.post() |
| 02/05/2026 | Suppression 0 dépendance admin dans templates v2/ | stable | Audit complet passé |
| 02/05/2026 | Suppression 0 dépendance admin dans templates documents/ | stable | Breadcrumbs remplacés |

## PROBLÈMES RENCONTRÉS & SOLUTIONS
| Date | Problème | Cause | Solution appliquée |
|------|----------|-------|--------------------|
| 02/05/2026 | SyntaxError escaped quotes dans views | Script Python avait écrit \' au lieu de ' | Remplacement byte-level |
| 02/05/2026 | PermissionError log rotation | Windows file lock sur django.log | Non bloquant, ignoré |
| 02/05/2026 | Monkey-patch ENSMGAdminSite peu fiable | core/apps.py ready() tardif | Middleware de restriction à la place |

## POINTS DE VIGILANCE
- Le superadmin (is_superuser=True) est BLOQUÉ des vues inventory_view=True → ne jamais oublier ce flag
- login_url = '/admin/login/' dans FrontendView — pas encore de page de login frontend custom
- exercices_ouverts vient du context processor core/context_processors.py, pas de FrontendView
- Les templates documents/ utilisent @staff_member_required, pas FrontendView
- Le projet D:\PROJETS\ENSMG\... est une copie de sauvegarde NON synchronisée

## DETTE TECHNIQUE EN COURS
| Priorité | Problème | Impact | Effort |
|----------|----------|--------|--------|
| HAUTE | Pas de bouton logout dans le frontend | Utilisateur bloqué | S |
| HAUTE | Pas de page login frontend (utilise /admin/login/) | Dépendance résiduelle admin | M |
| MOYENNE | Référentiels (dépôts, services, fournisseurs, donateurs) sans CRUD frontend | Données non modifiables sans admin | L |
| MOYENNE | Sorties définitives (destruction, vente, certificat, fin de gestion) sans vues frontend | Fonctionnalités manquantes | L |
| FAIBLE | Pas de Git sur le projet actif (backup manuel sur D:) | Risque de perte de travail | S |

## NOTES DE SESSION
### Session 02/05/2026
- Implémentation complète du système de rôles et permissions
- Création gestion utilisateurs frontend (UserListView, UserCreateView, UserEditView, UserDeleteView)
- Audit et nettoyage 0 admin dans ~30 templates
- ProfilView étendue avec POST pour changement de mot de passe
- En cours au moment de la pause : 3 fonctionnalités topbar (logout, dropdown profil, sélecteur exercices)
