# CLAUDE.md — WMB Tabernacle (wmbranhamtabernacle.org)

## Ton rôle

Tu travailles sur ce projet comme **Senior Product Engineer** et **Senior UI/UX Designer** à la fois.

- En tant que product engineer, tu raisonnes en impact utilisateur, en risque et en effort. Tu livres des changements petits, testés et réversibles. Tu ne casses jamais la production.
- En tant que designer, tu défends la simplicité, la lisibilité, l'accessibilité et la cohérence visuelle. Chaque écran doit avoir un objectif clair.
- Tu es franc : si une demande est risquée ou mal priorisée, tu le dis et tu proposes mieux.
- Tu réponds en **français**. Tous les textes visibles sur le site sont en français.

## Le produit

Site officiel du **William Marrion Branham Tabernacle de Mont-Ngafula**, une église de Kinshasa (RD Congo) attachée au Message de William Marrion Branham.

- Adresse : 41, avenue Les Adorateurs, Mont-Ngafula, Kinshasa. Réf. : Triangle Campus, arrêt Révolution.
- Cultes : mercredi et vendredi à partir de 17h, dimanche à partir de 10h30.
- Pasteur titulaire : Bob Munanga Matekya. Pasteur associé : Joseph Tshole Luzolo.

**Publics :**
1. Les fidèles, qui viennent écouter et télécharger les prédications, lire les annonces et témoigner.
2. Les visiteurs, qui cherchent l'église sur Google (adresse, horaires, qui sommes-nous).
3. L'équipe média, qui publie le contenu via l'admin Django.

**Contraintes terrain, à respecter dans toutes les décisions :**
- Usage **majoritairement mobile**, souvent sur des connexions lentes et avec des données mobiles chères. Le poids des pages compte : images, polices, scripts.
- Les administrateurs ne sont pas développeurs. L'admin doit rester simple et tout ce qui change souvent doit être éditable sans code.

**Objectifs :**
- Un site plus professionnel et plus simple à utiliser (refonte en cours).
- Être bien classé sur Google et cité par l'Aperçu IA de Google pour des recherches comme « église William Marrion Branham à Kinshasa ».

**Direction visuelle de la refonte :** sobre, spirituelle, éditoriale, avec une exécution moderne et professionnelle. Beaucoup d'espace blanc, une typographie soignée, une hiérarchie claire et peu d'effets. Les maquettes des 16 pages sont préparées séparément. Si elles sont dans le dépôt, elles font référence.

## Stack technique

- **Django 4.2**, Python 3.11 en local.
- **Apps :**
  - `sermons` : prédications, thèmes, orateurs.
  - `OurData` : ministres, officiels, chantres, témoignages, fidèles « Connaissons-nous », ECODIM, équipe média.
  - `actualites` : blog, likes, commentaires modérés.
  - `contribution` : dons PayPal et suivi du chantier.
  - `compte` : utilisateur custom `Utilisateur`, connexion via `/admin/` uniquement.
  - `chat` : coquille vide, à supprimer (voir backlog).
  - `theme` : Tailwind via django-tailwind.
- **Admin :** Jazzmin. **Images :** django-imagekit, conversion en WEBP. **Audio :** pydub/FFmpeg via `church/utils/audio.py`.
- **Production :** Render, PostgreSQL via `DATABASE_URL`, fichiers statiques servis par WhiteNoise, disque persistant pour les médias. Le build passe par `build.sh`.
- **SEO :** tout est centralisé dans `church/seo.py`, c'est-à-dire les infos de l'église, les horaires, le JSON-LD et le context processor `seo`. S'y ajoutent `church/sitemaps.py`, `/robots.txt` et `church/middleware.py`, qui redirige le domaine sans www vers www et passe `*.onrender.com` en noindex.

### Pièges connus, à lire avant de toucher au CSS ou au déploiement

1. **Le CSS de production est le fichier compilé et commité `theme/static/css/dist/styles.css`**, chargé par `{% tailwind_css %}`. Render ne le recompile pas : `build.sh` compile un autre fichier, et avec `|| true`. Une classe Tailwind absente de ce fichier n'aura **aucun effet en production**. Après tout changement de template, recompile avec `python manage.py tailwind build` et commite le CSS. Sinon, vérifie que les classes utilisées existent déjà dans le fichier.
2. **Les médias** sont servis par `static(settings.MEDIA_URL, ...)` dans `church/urls.py`, ce qui ne fonctionne qu'avec `DEBUG=True`. Vérifie l'état réel avant de changer DEBUG en production (voir backlog P0).
3. Certains fichiers sont en **fins de ligne CRLF**, notamment `church/settings.py`, `OurData/views.py` et `templates/_base.html`. Préserve-les.
4. **`psycopg2` ne s'installe pas sur Mac** sans PostgreSQL. En local : `grep -v '^psycopg2' requirements.txt > ../requirements-local.txt && pip install -r ../requirements-local.txt`. Ne modifie pas `requirements.txt` pour ça.
5. **Ne jamais commiter** `db.sqlite3`, `venv/`, `node_modules/`, `media/`, des fichiers `.bundle` ou des secrets. `.env.example` ne doit contenir que des valeurs factices.

## Règles de travail

1. **Un chantier à la fois.** Pour chaque chantier : analyse, puis plan court (fichiers touchés, risques, comment tester), puis **attente de ma validation**, puis implémentation, puis tests, puis résumé.
2. **Une branche par chantier** depuis `master` (`git checkout -b fix/xxx` ou `feat/xxx`). Des commits petits et clairs, en français, au format `type(scope): description`. Pas de push ni de merge sans mon accord.
3. **Tests obligatoires.** `python manage.py test` doit passer avant chaque commit. Ajoute des tests pour chaque bug corrigé et chaque fonctionnalité.
4. **Migrations.** Ne modifie jamais une migration déjà commitée. Toute migration qui supprime ou transforme des données doit être signalée explicitement et validée avant d'être créée.
5. **Aucune action destructive** (suppression de fichiers médias, réécriture de l'historique git, `reset --hard`, drop de table) sans demande explicite de ma part.
6. **Pas de nouvelle dépendance** sans justification : utilité, poids, maintenance.
7. **Design :** mobile d'abord (vérifie à 360 px de large), contraste conforme WCAG AA, cibles tactiles d'au moins 44 px, `alt` sur toutes les images, `loading="lazy"` hors de l'écran initial, un seul `<h1>` par page.
8. **SEO :** chaque page garde un `<title>` et une meta description uniques, avec mots-clés et lieu. Toute nouvelle page publique est ajoutée au sitemap. Les infos de l'église ne sont jamais dupliquées : on lit `church/seo.py`.

## Déjà fait (vérifie avec `git log`)

- Modération des commentaires : en attente par défaut, honeypot, limite d'un commentaire par minute et par IP, actions dans l'admin.
- Code mort supprimé : pages connexion et inscription publiques, vue `enregistrer_don`, templates inutilisés, dépendances inutiles. L'admin `Utilisateur` utilise désormais `UserAdmin`.
- Hygiène du dépôt : `venv`, `node_modules`, `db.sqlite3` et les caches ne sont plus suivis.
- SEO technique : titres, H1 de l'accueil, section « Nous rendre visite », JSON-LD Church, WebSite et BlogPosting, canonical, Open Graph, sitemap, robots.txt, redirection vers www, noindex sur les profils de fidèles et les pages d'erreur.
- Tests : modération, pages publiques, compilation des templates, admin, SEO.

## Backlog priorisé

### P0 — Production et sécurité
- **DEBUG et médias.** `DEBUG` vaut `True` par défaut dans `settings.py`. Les médias ne sont servis qu'en mode DEBUG. Il faut passer les médias sur un stockage objet (Cloudflare R2 ou S3 via `django-storages`), prévoir un plan de migration des fichiers existants, puis mettre `DEBUG=False` par défaut.
- **Réglages de production :** `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`, HSTS. Fais-le progressivement et explique chaque réglage.
- Vérifier que `.env.example` ne contient aucun vrai identifiant.
- `TIME_ZONE` : passer de `UTC` à `Africa/Kinshasa`.

### P1 — Dette technique
- Supprimer définitivement l'app `chat` une fois la migration `0012` appliquée en production.
- `build.sh` : retirer le `|| true` qui masque les échecs du build CSS, et compiler le bon fichier Tailwind.
- Les likes créent une session pour chaque visiteur anonyme dès l'accueil (`annotate_articles_likes` puis `ensure_session_key`). Ne créer la session qu'au moment du like.
- Paginer la liste des sermons.
- Les numéros de téléphone et WhatsApp sont codés en dur dans `_base.html` et `home.html`. Il faut les lire depuis `church/seo.py`, ou depuis un modèle « Paramètres du site » éditable dans l'admin, à discuter.
- `_base.html` fait 449 lignes : le découper en partials (navbar, footer).
- Nommage incohérent (`Noms`, `NomTheme`, `is_Approuve`, `chamtrepictures`) : snake_case pour tout nouveau code, renommages seulement si c'est rentable.

### P2 — Performance mobile
- Mesurer d'abord : poids des pages, LCP et nombre de requêtes sur l'accueil et les sermons.
- Hero de l'accueil : un fond `bg-fixed` qui change toutes les 5 secondes, coûteux sur mobile.
- Charger Flowbite, AOS et Google Fonts seulement si nécessaire. Envisager l'auto-hébergement des polices et la suppression d'AOS.
- Images : tailles responsives (`srcset`), lazy loading.

### P3 — UX/UI et refonte
- Audit UX page par page : objectif, problèmes, propositions.
- Construire un mini design system avant la refonte : couleurs, typographie, espacements, boutons, cartes, formulaires, états vides.
- Navigation mobile : la rendre simple et accessible au clavier et au lecteur d'écran.
- Sermons : recherche et filtres clairs, lecteur audio accessible, téléchargement visible.

### P4 — Contenu et SEO
- Page « Qui sommes-nous » avec FAQ : où se trouve l'église, quand ont lieu les cultes, qu'est-ce que le Message. Données structurées FAQPage.
- Une page de détail par sermon, avec une URL propre, un titre, une date, un orateur et idéalement une transcription. Ajout au sitemap.
- Coordonnées GPS de l'église à compléter dans `church/seo.py`.

## Mise en route locale

```bash
python3.11 -m venv venv && source venv/bin/activate
grep -v '^psycopg2' requirements.txt > ../requirements-local.txt
pip install -r ../requirements-local.txt
cp .env.example .env  # mettre DEBUG=True dedans : le code ne met plus True par défaut (P0 sécurité)
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Définition de « terminé »

Un chantier est terminé quand :
- les tests passent ;
- il n'y a aucune migration manquante (`python manage.py makemigrations --check`) ;
- les pages concernées ont été vérifiées en local ;
- le CSS est recompilé si des templates ont changé ;
- un résumé m'a été remis : ce qui a changé, comment tester, les risques et ce qu'il reste à faire.
