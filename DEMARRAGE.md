# Démarrage du projet — WMB Tabernacle

Guide pour lancer le site **churchWebsite** en local (Django + Tailwind CSS).

---

## Prérequis

| Outil | Version recommandée |
|-------|---------------------|
| **Python** | 3.11+ |
| **Node.js** | 18+ (20 recommandé) |
| **npm** | inclus avec Node.js |
| **Git** | pour cloner le dépôt |

---

## 1. Cloner le projet

```bash
git clone <url-du-depot> churchWebsite
cd churchWebsite
```

---

## 2. Environnement virtuel Python

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## 3. Variables d'environnement

Copier le fichier d'exemple et l'adapter :

```bash
cp .env.example .env
```

Contenu minimal pour le **développement local** :

```env
SECRET_KEY=votre-cle-secrete-ici
DEBUG=True
```

> En local, la base **SQLite** (`db.sqlite3`) est utilisée par défaut.  
> En production (Render), définir aussi `DATABASE_URL` et éventuellement `MEDIA_ROOT`.

Générer une clé secrète :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 4. Base de données

Appliquer les migrations :

```bash
python manage.py migrate
```

Créer un compte administrateur (accès `/admin/`) :

```bash
python manage.py createsuperuser
```

---

## 5. CSS Tailwind (obligatoire)

Le site utilise **django-tailwind** (app `theme`). Les styles sont compilés dans  
`theme/static/css/dist/styles.css`.

### Première installation des paquets npm

```bash
python manage.py tailwind install
```

### Compiler le CSS (à faire après chaque changement de classes dans les templates)

```bash
python manage.py tailwind build
```

### Mode développement (recompilation automatique)

```bash
python manage.py tailwind start
```

> Si `tailwind start` échoue avec `Error: spawn tailwindcss EACCES`, utiliser plutôt  
> `python manage.py tailwind build` après chaque modification, ou :
>
> ```bash
> cd theme/static_src
> chmod +x node_modules/.bin/*
> npm run dev
> ```

**Important :** sans `tailwind build`, les nouvelles pages (blog, accueil, etc.) s'affichent sans mise en forme.

---

## 6. Lancer le serveur de développement

Dans un **second terminal** (le premier peut rester sur `tailwind start` si utilisé) :

```bash
source venv/bin/activate
python manage.py runserver
```

Ouvrir dans le navigateur :

| Page | URL |
|------|-----|
| Accueil | http://127.0.0.1:8000/ |
| Blog | http://127.0.0.1:8000/blog/ |
| Admin | http://127.0.0.1:8000/admin/ |

Rechargement forcé après un `tailwind build` : **Cmd+Shift+R** (Mac) ou **Ctrl+F5**.

---

## 7. Fichiers médias (images uploadées)

Les images du blog, sermons, etc. sont servies depuis le dossier `media/` en développement.  
Vérifier que de nouveaux uploads ont bien une **image de couverture** dans l'admin (`Actualités > Articles`).

---

## Récapitulatif — démarrage rapide

```bash
cd churchWebsite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py tailwind install
python manage.py tailwind build
python manage.py createsuperuser   # optionnel
python manage.py runserver
```

---

## Production (aperçu)

```bash
python manage.py collectstatic --noinput
python manage.py tailwind build
# Variables : DEBUG=False, SECRET_KEY, DATABASE_URL, MEDIA_ROOT
# Serveur : gunicorn church.wsgi (voir configuration Render / hébergeur)
```

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Design cassé / HTML brut | `python manage.py tailwind build` puis recharger le cache |
| `Couldn't import Django` | Activer le venv : `source venv/bin/activate` |
| `tailwind start` → EACCES | `chmod +x theme/static_src/node_modules/.bin/*` ou utiliser `tailwind build` |
| Images blog étranges | Remplacer les captures d'écran par de vraies images dans l'admin |
| Erreur base PostgreSQL en local | Retirer `DATABASE_URL` du `.env` pour utiliser SQLite |

---

## Structure utile

```
churchWebsite/
├── church/           # settings, urls, vues principales
├── actualites/       # blog, articles, likes, commentaires
├── templates/        # templates HTML
├── theme/            # app Tailwind (CSS compilé dans theme/static/css/dist/)
├── media/            # fichiers uploadés
├── manage.py
├── requirements.txt
└── .env              # variables locales (non versionné)
```
