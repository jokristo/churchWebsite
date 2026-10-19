# Guide de déploiement sur Render

Ce guide te permet de déployer WMB Tab sur Render avec **PostgreSQL**, et les médias (audios, images) sur **Cloudflare R2**.
Le **Persistent Disk** ne sert plus qu'à l'ancienne configuration et au retour arrière (voir l'étape 7).

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
| **Build Command** | `./build.sh` (installe FFmpeg, les dépendances, compile le CSS Tailwind, collectstatic et migrate) |
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
| `DEBUG` | *(ne pas définir)* | `False` par défaut ; ne jamais mettre `True` en production |
| `DATABASE_URL` | *(copie depuis PostgreSQL)* | Internal Database URL de l’étape 1 |
| `MEDIA_ROOT` | `/data/media` | Chemin sur le disque persistant (ancienne configuration, gardé pour le retour arrière) |
| `SECURITE_PRODUCTION` | `1` | HTTPS strict, cookies sécurisés, HSTS (voir l'étape 8) |

Les variables du stockage R2 sont décrites à l'étape 7.

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

## Étape 7 : Médias sur Cloudflare R2

Les audios et les images envoyés depuis l'admin sont stockés dans le bucket R2 `wmbtab-media`
et servis par `https://media.wmbranhamtabernacle.org` : rapide (cache Cloudflare), lecture
partielle des audios (on peut avancer dans un sermon) et bande passante gratuite.
Le choix du stockage est fait dans `church/stockage.py`.

### Variables d'environnement (Render → Environment)

| Variable | Valeur |
|----------|--------|
| `AWS_ACCESS_KEY_ID` | Access Key ID du jeton R2 (R2 → Manage API Tokens) |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key du même jeton (affichée une seule fois) |
| `AWS_STORAGE_BUCKET_NAME` | `wmbtab-media` |
| `AWS_S3_ENDPOINT_URL` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`, **sans** `/wmbtab-media` à la fin |
| `AWS_S3_CUSTOM_DOMAIN` | `media.wmbranhamtabernacle.org` (sans `https://`) |
| `MEDIA_STORAGE` | `r2` — **uniquement à l'étape « Bascule » ci-dessous** |

Sans `MEDIA_STORAGE=r2`, le site garde le disque, même si les autres variables sont présentes.
Le jeton R2 doit avoir la permission « Object Read & Write », limitée au bucket `wmbtab-media`.

### Bascule (une seule fois)

Toutes les commandes se lancent dans **Render → Shell**.

1. **Déployer** le code qui contient `church/stockage.py` sans définir `MEDIA_STORAGE` :
   rien ne change pour les visiteurs.
2. **Diagnostic** : écrit un fichier de test dans R2, le relit par le domaine public,
   vérifie `Content-Type`, `Cache-Control` et la lecture partielle (Range), puis le supprime.
   ```bash
   python manage.py migrer_medias --diagnostic
   ```
   Ne pas continuer tant que la dernière ligne n'est pas « R2 est prêt pour la bascule ».
3. **Simulation** : liste les fichiers du disque qui seront copiés.
   ```bash
   python manage.py migrer_medias --dry-run
   ```
4. **Prévenir l'équipe média** : aucun envoi de fichier dans l'admin jusqu'à la fin de l'étape 7.
5. **Copie puis vérification** (taille et empreinte MD5 de chaque fichier) :
   ```bash
   python manage.py migrer_medias
   python manage.py migrer_medias --verifier
   ```
   La copie est rejouable : un fichier déjà présent à l'identique est ignoré, rien n'est
   jamais écrasé (un fichier différent est signalé comme conflit).
6. **Basculer** : ajouter `MEDIA_STORAGE=r2` dans Render → Environment (redéploiement automatique).
7. **Rattraper** un éventuel envoi fait pendant la bascule, puis contrôler :
   ```bash
   python manage.py migrer_medias && python manage.py migrer_medias --verifier
   ```
8. **Contrôles** depuis n'importe quel ordinateur :
   ```bash
   # l'URL d'un audio sur /sermons/ doit commencer par https://media.wmbranhamtabernacle.org/
   curl -sI -H "Range: bytes=0-1023" https://media.wmbranhamtabernacle.org/audio/<fichier>.mp3
   # attendu : HTTP 206, Content-Type audio/mpeg, Cache-Control public, max-age=31536000, immutable
   curl -sI https://www.wmbranhamtabernacle.org/media/audio/<fichier>.mp3
   # attendu : 301 vers https://media.wmbranhamtabernacle.org/... (anciens liens conservés)
   ```
   Puis envoyer un fichier test dans l'admin et vérifier qu'il s'affiche.

### Retour arrière

1. Recopier vers le disque ce qui a été envoyé sur R2 depuis la bascule :
   ```bash
   python manage.py migrer_medias --sens r2-vers-disque
   ```
2. Supprimer `MEDIA_STORAGE` dans Render → Environment. Le site sert de nouveau les fichiers du disque.

Le disque persistant reste **intact au moins deux semaines** après la bascule. Ensuite seulement :
supprimer le disque (Settings → Disks) et la variable `MEDIA_ROOT`.

**État : bascule faite le 19/10/2026.** Disque à garder jusqu'au 2 novembre 2026.

---

## Étape 8 : Sécurité de production

À faire dans l'ordre, en vérifiant le site entre chaque étape. Chaque étape se défait
en retirant la variable correspondante.

1. **Désactiver le mode debug** : supprimer `DEBUG=True` (ou mettre `DEBUG=False`).
   Contrôle : une page inexistante affiche la page 404 du site, et non une page
   technique jaune de Django.
2. **Activer le HTTPS strict** : ajouter `SECURITE_PRODUCTION=1`. Cela active :

   | Réglage | Effet |
   |---------|-------|
   | `SECURE_PROXY_SSL_HEADER` | Django reconnaît le HTTPS terminé par Render (en-tête `X-Forwarded-Proto`) |
   | `SECURE_SSL_REDIRECT` | toute adresse `http://` est redirigée vers `https://` |
   | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | les cookies de l'admin ne circulent jamais en clair |
   | HSTS 1 heure | le navigateur refuse le HTTP pendant 1 heure après une visite |

   Contrôles :
   ```bash
   curl -sI http://www.wmbranhamtabernacle.org/ | grep -iE "^(HTTP|location)"
   # attendu : 301 vers https://www.wmbranhamtabernacle.org/ (une seule redirection)
   curl -sI https://www.wmbranhamtabernacle.org/ | grep -i strict-transport-security
   # attendu : max-age=3600
   ```
   Puis se connecter à l'admin et enregistrer une modification.
3. **Allonger HSTS par étapes**, après une semaine sans problème : `HSTS_SECONDES=2592000`
   (1 mois), puis `HSTS_SECONDES=31536000` et `HSTS_SOUS_DOMAINES=1` (1 an, sous-domaines
   compris). Ne jamais demander l'inscription « preload » : elle est quasi irréversible.

Retour arrière : supprimer `SECURITE_PRODUCTION`. Les navigateurs qui ont déjà reçu
l'en-tête HSTS continuent d'exiger le HTTPS jusqu'à son expiration (1 heure au départ).

`CSRF_TRUSTED_ORIGINS` (les deux domaines du site et `*.onrender.com`) est toujours actif.

---

## Étape 9 : Compression des audios

Chaque audio envoyé dans l'admin (sermons, témoignages) est enregistré tel quel, puis
compressé **en arrière-plan** en MP3 mono 64 kbps : la page de l'admin répond tout de
suite, et le fichier compressé remplace l'original au bout de une à trois minutes.
L'original reste dans le stockage. La colonne « Compression audio » de l'admin indique
l'état ; l'action « Compresser à nouveau l'audio » relance un traitement.

| Variable | Valeur par défaut | Rôle |
|----------|-------------------|------|
| `AUDIO_COMPRESSION` | `1` | `0` coupe la compression sans redéployer (les audios sont gardés tels quels) |
| `AUDIO_DEBIT` | `64k` | débit du MP3 mono produit (`96k` pour une meilleure qualité musicale) |

Dans le Shell :
```bash
python manage.py compresser_audios --dry-run      # ce qui serait traité
python manage.py compresser_audios                # en attente + traitements interrompus (redéploiement)
python manage.py compresser_audios --existants    # + audios envoyés avant cette fonctionnalité
python manage.py compresser_audios --echecs       # + nouvel essai des échecs
```

**Limite :** Cloudflare refuse les envois de plus de 100 Mo. Exporter les sermons en MP3
mono 64 à 128 kbps avant de les envoyer (un sermon de 2 h en 96 kbps fait environ 85 Mo).

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
| Persistent Disk 5 GB | ~1,50 $/mois, à supprimer deux semaines après la bascule R2 |
| Cloudflare R2 | 0 $ jusqu'à 10 Go stockés, bande passante sortante toujours gratuite |
| **Total** | **~1,50 $/mois, puis 0 $** |

---

## Dépannage

- **Erreur de build** : vérifie que `build.sh` est exécutable (`chmod +x build.sh`)
- **500 erreur** : vérifie les logs dans Render → **Logs**
- **Médias non affichés (disque)** : vérifie que `MEDIA_ROOT=/data/media` et que le disque est bien monté
- **Médias non affichés (R2)** : lance `python manage.py migrer_medias --diagnostic` dans le Shell ; il indique l'étape qui échoue
- **`ImproperlyConfigured` au démarrage** : une variable R2 manque ou est mal formée (endpoint avec le nom du bucket, domaine avec `https://`) ; le message indique laquelle
- **Le CSS ne se met pas à jour** : vérifie que la Build Command est bien `./build.sh` (et seulement elle : `build.sh` fait déjà pip, Tailwind, collectstatic et migrate)
- **Audio resté « En attente » ou « En cours »** : le serveur a redémarré pendant la compression ; lancer `python manage.py compresser_audios`
- **Audio en « Échec »** : le détail est dans l'admin (fichier illisible, délai dépassé) ; l'original reste écoutable
