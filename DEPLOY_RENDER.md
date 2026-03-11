# Guide de déploiement sur Render

Ce guide te permet de déployer WMB Tab sur Render avec **PostgreSQL** et **Persistent Disk**.

---

## Étape 1 : Créer la base PostgreSQL

1. Va sur [render.com](https://render.com) et connecte-toi
2. **Dashboard** → **New** → **PostgreSQL**
3. Configure :
   - **Name** : `wmbtab-db` (ou autre)
   - **Database** : `wmbtab`
   - **User** : (généré automatiquement)
   - **Region** : choisis le plus proche (ex: Frankfurt)
   - **Plan** : Free (pour commencer)
4. Clique sur **Create Database**
5. Une fois créée, note l’**Internal Database URL** (tu en auras besoin plus tard)

---

## Étape 2 : Créer le Web Service

1. **Dashboard** → **New** → **Web Service**
2. Connecte ton repo GitHub (churchWebsite)
3. Configure :

| Paramètre | Valeur |
|-----------|--------|
| **Name** | `wmbtab` |
| **Region** | Même que la base |
| **Branch** | `main` (ou ta branche) |
| **Runtime** | Python 3 |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn church.wsgi:application` |

---

## Étape 3 : Ajouter le Persistent Disk

1. Dans ton Web Service → **Settings** → **Disks**
2. Clique sur **Add Disk**
3. Configure :
   - **Name** : `media`
   - **Mount Path** : `/data`
   - **Size** : 5 GB (ou 10 GB pour ~3 $/mois)
4. Clique sur **Create**

---

## Étape 4 : Variables d'environnement

Dans le Web Service → **Environment** → **Add Environment Variable** :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `SECRET_KEY` | *(génère une clé)* | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | |
| `DATABASE_URL` | *(copie depuis PostgreSQL)* | Internal Database URL de l’étape 1 |
| `MEDIA_ROOT` | `/data/media` | Chemin sur le disque persistant |

**Pour DATABASE_URL** : dans ton service PostgreSQL → **Connect** → copie **Internal Database URL**.

---

## Étape 5 : Lier PostgreSQL au Web Service

1. Dans le Web Service → **Environment**
2. Clique sur **Link Database** (ou ajoute manuellement `DATABASE_URL`)
3. Sélectionne ta base PostgreSQL

---

## Étape 6 : Déployer

1. Clique sur **Manual Deploy** → **Deploy latest commit**
2. Attends la fin du build (2–5 min)
3. Ton site est en ligne sur `https://wmbtab.onrender.com` (ou le nom de ton service)

---

## Créer un superutilisateur

1. Dans le Web Service → **Shell** (ou utilise Render Shell)
2. Exécute :
   ```bash
   python manage.py createsuperuser
   ```
3. Suis les instructions pour créer ton compte admin

---

## Résumé des coûts (estimés)

| Service | Coût |
|---------|------|
| Web Service (Free) | 0 $ |
| PostgreSQL (Free) | 0 $ |
| Persistent Disk 5 GB | ~1,50 $/mois |
| **Total** | **~1,50 $/mois** |

---

## Dépannage

- **Erreur de build** : vérifie que `build.sh` est exécutable (`chmod +x build.sh`)
- **500 erreur** : vérifie les logs dans Render → **Logs**
- **Médias non affichés** : vérifie que `MEDIA_ROOT=/data/media` et que le disque est bien monté
