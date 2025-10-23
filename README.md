# Supervision des obsolescences

MVP complet pour superviser l'obsolescence des applications et de leurs dépendances. Le projet expose une API REST FastAPI, un frontend statique avec Chart.js ainsi qu'un scheduler d'alertes e-mail/Teams.

## Fonctionnalités principales

- **Inventaire centralisé** : CRUD projets/applications/versions/dépendances, normalisation via catalogue des technologies, import et export CSV.
- **Dashboard analytics** : indicateurs de risques, histogramme des échéances, alertes sur dépendances partagées et top 10 des priorités.
- **Notifications** : envoi e-mail (SMTP OVH) et webhook Microsoft Teams, journalisation des notifications, planification quotidienne via APScheduler.
- **Collaboration** : timeline des changements, commentaires internes, plans d'action, référentiel d'actions correctives, gestion des utilisateurs et des rôles.
- **Administration** : paramètres globaux, authentification JWT (bcrypt), rôles lecteur/contributeur/admin, journalisation JSON.

## Stack technique

- Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, APScheduler.
- Frontend HTML5 + TailwindCSS via CDN, Alpine.js pour l'interactivité, Chart.js pour les graphiques.
- Base de données MariaDB ou SQLite (par défaut). Les scripts Alembic permettent la portabilité.
- Notifications : `smtplib` pour SMTP, `requests` pour webhook Teams.

## Prérequis

- Python 3.12+
- MariaDB 10.6+ (ou SQLite pour un test rapide)
- Accès SMTP (OVH) et webhook Microsoft Teams optionnels

## Installation

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseignez les variables nécessaires dans `.env` :

- `SECRET_KEY` : clé aléatoire (openssl rand -hex 32)
- `DATABASE_URL` : ex. `mariadb+pymysql://user:pwd@localhost/obsolescences`
- `SMTP_*` : configuration OVH (optionnelle en dev)
- `TEAMS_WEBHOOK_URL` : URL du connecteur Teams (optionnel)
- `BACKEND_CORS_ORIGINS` : origines autorisées pour le frontend

## Base de données & migrations

Initialisez la base :

```bash
alembic upgrade head
```

En cas de modification du modèle, générez une migration :

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Création du premier administrateur

```bash
python scripts/create_admin.py --name "Admin" --email admin@example.com --password "ChangeMe123!"
```

## Lancer l'application

```bash
uvicorn app.main:app --reload
```

- API : http://localhost:8000/api/v1
- Documentation OpenAPI : http://localhost:8000/api/v1/openapi.json
- Frontend : http://localhost:8000/

Connectez-vous via le formulaire (login / mot de passe créés précédemment). Le token JWT est stocké en localStorage et utilisé pour toutes les requêtes.

## Scheduler & notifications

Le planificateur APScheduler démarre avec l'application (job quotidien 07:00). Il parcourt les versions/dépendances dont la fin de support est inférieure au seuil (`ALERT_THRESHOLD_MONTHS`) et envoie une notification e-mail + enregistre la trace. Les notifications peuvent aussi être déclenchées manuellement via l'API `/notifications/*`.

## Import / export CSV

Modèle attendu (UTF-8) :

```
project_name,project_team,project_contact,application_name,application_description,application_owner,application_criticity,application_status,version_number,version_end_of_support,version_end_of_contract,dependency_category,dependency_name,dependency_version,dependency_end_of_support
```

- `application_criticity` : `faible|moyenne|haute|critique`
- `application_status` : `active|obsolète|retirée`
- `dependency_category` : `langage|runtime|os|middleware|librairie|autre`
- Dates au format `YYYY-MM-DD` ou `DD/MM/YYYY`

Télécharger le modèle : `GET /api/v1/inventory/template`
Importer : `POST /api/v1/inventory/import`
Exporter : `GET /api/v1/inventory/export`

## Structure API (extraits)

| Ressource | Endpoint | Rôle requis |
|-----------|----------|-------------|
| Authentification | `POST /api/v1/auth/token` | Public |
| Projets | `GET /api/v1/projects/` | Lecteur |
| Applications | `GET /api/v1/applications/` | Lecteur |
| Versions / Dépendances | `POST /api/v1/versions/` | Contributeur |
| Plans d'action | `POST /api/v1/action-plans/` | Contributeur |
| Commentaires | `POST /api/v1/comments/` | Contributeur/Owner |
| Notifications | `POST /api/v1/notifications/email` | Contributeur |
| Paramètres | `GET /api/v1/settings/` | Admin |
| Utilisateurs | `POST /api/v1/users/` | Admin |

Toutes les routes nécessitent le header `Authorization: Bearer <token>` sauf le login.

## Logs & observabilité

- Logs JSON sur stdout (niveau configuré via `LOG_LEVEL`).
- Notifications historisées dans la table `notifications`.
- Timeline détaillée (table `timeline_events`).

## Déploiement recommandé

1. VM OVH (Ubuntu 22.04) derrière Nginx (reverse proxy + TLS Let's Encrypt).
2. Gunicorn + Uvicorn workers pour servir l'API (`gunicorn -k uvicorn.workers.UvicornWorker app.main:app`).
3. MariaDB managé ou service OVH, sauvegarde quotidienne (mysqldump). Snapshot VM hebdomadaire.
4. Logrotate sur `/var/log/obsolescences/*.log` si redirection fichier.
5. Services systemd : `obsolescences-api.service` (Gunicorn) et `obsolescences-scheduler.service` si besoin de planificateur externe.

## Tests manuels conseillés

- Création d'un projet, d'une application et de dépendances via API.
- Import CSV et vérification de la déduplication (même application + projet).
- Envoi de notification e-mail/Teams en sandbox.
- Vérification du dashboard : métriques, graphiques, top priorités.
- Export CSV et ouverture dans Excel.

## Roadmap (post-MVP)

- Synchronisation CMDB / CI-CD (import automatisé).
- Scoring risque/coût, intégration BI (PowerBI/Tableau).
- API d'export temps-réel pour outils internes (Jira, ITSM).
- Intégration LDAP/SSO et audit avancé.
