# SPEC.md — Spécifications ENSMG Comptabilité des Matières

Dernière mise à jour : 02/05/2026

## PRÉSENTATION DU PROJET

Application web Django de comptabilité des matières pour l'ENSMG (École Nationale Supérieure des Mines et de la Géologie du Sénégal). Gestion complète du cycle de vie des matières : entrées (achats, dons, legs, dotations), stocks, sorties, transferts, et génération de documents réglementaires.

## STACK TECHNIQUE

- **Backend** : Django 5.2 / Python 3.x
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **PDF** : WeasyPrint
- **Frontend** : Templates Django (pas de framework JS — CSS vanilla inline)
- **Auth** : Django auth natif + système de rôles custom (core/roles.py)

## ARCHITECTURE

### Applications
- `core` — Modèles de base : Exercice, Sequence, FournisseurSequence, Unite, Depot, Fournisseur, Donateur, Service, ExternalSource, PendingRecord, Notification, AgentPermission
- `catalog` — Catalogue matières : Categorie, SousCategorie, Matiere, ComptePrincipal, CompteDivisionnaire, SousCompte
- `purchasing` — Entrées : Achat, LigneAchat, RetourFournisseur, LigneRetour, Don, LigneDon, Pret, LignePret, RetourPret, LigneRetourPret, ExternalStockEntry, ExternalStockEntryLine, LegsEntry, Dotation, LigneDotation
- `inventory` — Stock et mouvements : MouvementStock (+ sous-classes EntreeStock, SortieStock, StockInitial), StockCourant, OperationSortie, LigneOperationSortie, SortieCertificatAdmin, SortieFinGestion, OperationTransfert, LigneOperationTransfert, FicheAffectation
- `audit` — Application présente dans INSTALLED_APPS (modèles à compléter)
- `documents` — Génération PDF (vues de génération, templates WeasyPrint)
- `frontend` — Interface utilisateur principale (/app/)

### Système de rôles (core/roles.py)
| Rôle | Technique | Accès |
|------|-----------|-------|
| Super Administrateur | is_superuser=True, is_staff=True | Gestion utilisateurs, paramètres système — PAS l'inventaire (inventory_view=True bloqué) |
| Chef de service | is_staff=True + Groupe "Chef de service" | Tout l'inventaire + gestion agents + paramètres |
| Agent simple | Groupe "Agent simple" + AgentPermission | Sections autorisées par chef uniquement (22 permissions booléennes) |

### Permissions granulaires AgentPermission (22 champs)
- Catalogue : perm_categories, perm_matieres, perm_comptes
- Achats & Entrées : perm_achats, perm_dons, perm_legs, perm_dotations
- Prêts & Retours : perm_prets, perm_retours_fournisseurs
- Stock : perm_stock_courant, perm_stock_actuel, perm_mouvements, perm_sorties_stock, perm_transferts
- Sorties définitives : perm_sorties_definitives, perm_reforme
- Référentiels : perm_fournisseurs, perm_donateurs, perm_depots, perm_services, perm_unites
- Registres : perm_livre_journal

### Middleware custom
- `core.middleware.SuperadminAdminRestrictionMiddleware` — restreint le superadmin aux seules pages admin système (/admin/auth/)

### URLs principales
- `/` — Landing page (LandingView)
- `/admin/login/` — Page de connexion (Django admin login réutilisé)
- `/admin/` — Redirige vers /app/ si connecté, sinon vers /admin/login/
- `/app/` — Frontend principal (FrontendView, namespace `frontend`)
- `/app/users/` — Gestion utilisateurs (superadmin uniquement)
- `/app/agents/` — Gestion permissions agents (chef de service)
- `/app/profil/` — Profil + changement mot de passe
- `/documents/` — Génération documents PDF (namespace `documents`)
- `/core/` — URLs core (namespace `core`)
- `/admin/dashboard/` — Dashboard admin v1 (conservé)
- `/admin/comptes-imputation/` — Dashboard comptes d'imputation
- `/admin/categories/` — Dashboard catégories
- `/admin/services/` — Dashboard services
- `/admin/depots/` — Dashboard dépôts

### URLs frontend détaillées (/app/...)
| URL | Vue | active_page | inventory_view | agent_perm_key |
|-----|-----|-------------|----------------|----------------|
| `` | DashboardView | dashboard | — | — |
| `exercices/` | ExercicesListView | exercices | True | — |
| `categories/` | CategoriesListView | — | — | perm_categories |
| `matieres/` | MatieresListView | — | — | perm_matieres |
| `comptes/` | ComptesListView | — | — | perm_comptes |
| `achats/` | AchatsListView | — | True | perm_achats |
| `dons/` | DonsListView | — | True | perm_dons |
| `legs/` | LegsListView | — | True | perm_legs |
| `dotations/` | DotationsListView | — | True | perm_dotations |
| `prets/` | PretsListView | — | True | perm_prets |
| `retours-fournisseurs/` | RetoursFournisseursListView | — | True | perm_retours_fournisseurs |
| `mouvements/` | MouvementsListView | — | True | perm_mouvements |
| `stock/courant/` | StockCourantListView | — | True | perm_stock_courant |
| `stock/actuel/` | StockActuelListView | — | True | perm_stock_actuel |
| `stock/sorties/` | SortiesStockListView | — | True | perm_sorties_stock |
| `transferts/` | TransfertsListView | — | True | perm_transferts |
| `sorties-definitives/` | SortiesDefinitivesListView | — | True | perm_sorties_definitives |
| `reforme/` | ReformeListView | — | True | perm_reforme |
| `fournisseurs/` | FournisseursListView | — | — | perm_fournisseurs |
| `donateurs/` | DonateursListView | — | — | perm_donateurs |
| `depots/` | DepotsListView | — | — | perm_depots |
| `services/` | ServicesListView | — | — | perm_services |
| `unites/` | UnitesListView | — | — | perm_unites |
| `livre-journal/` | LivreJournalView | livre_journal | True | perm_livre_journal |
| `notifications/` | NotificationsView | notifications | — | — |
| `profil/` | ProfilView | profil | — | — |
| `parametres/` | SettingsView | settings | — | superadmin ou chef uniquement |
| `agents/` | AgentListView | — | — | chef_service |
| `users/` | UserListView | users | — | superadmin |

## MODÈLES CLÉS

### core.Exercice
- Champs : annee (unique), date_debut, date_fin (auto), statut (OUVERT/CLOS), code (auto : EX-{annee})
- Contrainte : un seul exercice OUVERT à la fois (UniqueConstraint)
- Méthodes de classe : courants(), courant_label()

### core.AgentPermission
- OneToOne avec User
- 22 champs booléens préfixés perm_
- Méthode perm_fields() pour affichage en template

### catalog.Matiere
- Liée à SousCategorie → Categorie
- Comptes d'imputation : ComptePrincipal → CompteDivisionnaire → SousCompte

### purchasing.Achat
- Codes auto-générés via FournisseurSequence (pattern : ACH-FOURNISSEUR-ANNEE-XXXXX)
- Lignes : LigneAchat (quantite, prix_unitaire, totaux HT/TVA/TTC recalculés)

### inventory.MouvementStock
- Modèle de base avec proxy classes : EntreeStock, SortieStock, StockInitial
- Alimenté par signaux post_save sur les modèles purchasing

### inventory.StockCourant
- Agrégat matiere + depot + exercice → quantite courante
- Mis à jour par signaux depuis MouvementStock

## FONCTIONNALITÉS

### Stables
- [x] Authentification et système de rôles (superadmin / chef de service / agent)
- [x] Sidebar et dashboard conditionnels par rôle
- [x] 22 permissions granulaires par agent (AgentPermission)
- [x] CRUD utilisateurs dans /app/users/ (superadmin)
- [x] Gestion permissions agents dans /app/agents/ (chef de service)
- [x] Changement de mot de passe sur /app/profil/
- [x] Liste achats, dons, legs, dotations, prêts, retours fournisseurs
- [x] Détail achat, don, legs, prêt
- [x] Stock courant, stock actuel, mouvements, sorties, transferts, sorties définitives, réforme
- [x] Catalogue (catégories, matières, comptes d'imputation, unités)
- [x] Référentiels (fournisseurs, donateurs, dépôts, services)
- [x] Grand Journal (paginé, 30 résultats/page)
- [x] Génération PDF (documents réglementaires via WeasyPrint)
- [x] Context processor exercices (exercices_all, exercices_ouverts, exercices_selected_ids, exercices_label)
- [x] 0 lien /admin/ dans les templates frontend v2/ et documents/

### À implémenter
- [ ] Bouton logout + dropdown profil dans topbar
- [ ] Sélecteur d'exercices interactif dans topbar (multi-select, filtre les données)
- [ ] Page login frontend custom (remplacer /admin/login/)
- [ ] CRUD frontend pour référentiels (dépôts, services, fournisseurs, donateurs)
- [ ] Vues frontend pour sorties définitives (destruction, vente, certificat, fin de gestion)

## CONVENTIONS

### Nommage
- Vues : `XxxListView`, `XxxDetailView`, `XxxCreateView`, `XxxEditView`, `XxxDeleteView`
- Templates v2 : `templates/v2/<section>/list.html`, `detail.html`
- URLs : snake_case, namespace `frontend:`
- active_page : string snake_case correspondant à l'identifiant sidebar

### Patterns établis
- Toute vue hérite de `FrontendView` (LoginRequiredMixin + contrôle rôle)
- `inventory_view = True` sur toutes les vues inventaire (bloque superadmin)
- `agent_perm_key = 'perm_xxx'` pour les vues nécessitant une permission agent
- `SuperadminRequiredMixin` pour les vues réservées au superadmin
- `ChefServiceRequiredMixin` pour les vues réservées au chef de service
- Toujours `select_related()` dans les querysets de liste
- Pagination avec `django.core.paginator.Paginator` (30 à 50 résultats/page)
- Logging via `logger = logging.getLogger(__name__)` — jamais de print()

### Score de santé (02/05/2026)
| Axe | Note | Justification |
|-----|------|---------------|
| Architecture | 7/10 | Bonne séparation apps, quelques vues trop chargées |
| Qualité code | 6/10 | Pas de tests, quelques except génériques |
| Tests | 1/10 | Aucun test écrit |
| Sécurité | 7/10 | Rôles bien implémentés, login via admin encore |
| Performance | 6/10 | select_related utilisé, pas de cache, pas de pagination partout |
| Maintenabilité | 7/10 | CLAUDE.md, conventions claires, SPEC/MEMORY à jour |
| Infrastructure | 4/10 | Pas de Git sur projet actif, pas de CI/CD |
| **Global** | **5.4/10** | Fonctionnel mais sans filet de sécurité (tests + Git) |
