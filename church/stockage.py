"""Choix du stockage des médias (audios, images), piloté par l'environnement.

- Par défaut (développement, tests) : disque local, dans MEDIA_ROOT.
- MEDIA_STORAGE=r2 : Cloudflare R2 via django-storages (API S3), avec des URLs
  publiques non signées sur le domaine des médias.

L'activation est explicite : la simple présence des clés R2 dans un .env ne suffit
pas, pour qu'un poste de développement n'écrive jamais dans le bucket de production.
"""
import mimetypes

from django.core.exceptions import ImproperlyConfigured

# Types déclarés explicitement : la base mimetypes du système varie d'une machine à
# l'autre, et R2 renvoie le Content-Type enregistré à l'envoi.
for _type, _extension in (
    ("image/webp", ".webp"),
    ("audio/mpeg", ".mp3"),
    ("audio/mp4", ".m4a"),
):
    mimetypes.add_type(_type, _extension)

# Les fichiers ne sont jamais écrasés (file_overwrite=False) : un média remplacé
# reçoit un nouveau nom. On peut donc les mettre en cache un an sans risque.
CACHE_CONTROL = "public, max-age=31536000, immutable"

VARIABLES_R2 = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_ENDPOINT_URL",
    "AWS_S3_CUSTOM_DOMAIN",
)

STATICFILES = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
DISQUE = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
# Sous-classe de S3Storage (Content-Type fiable), dans l'app medias : ce module est
# importé par settings.py et ne doit pas charger django-storages ni boto3.
BACKEND_R2 = "medias.stockage.StockageR2"


def options_r2(env):
    manquantes = [nom for nom in VARIABLES_R2 if not (env.get(nom) or "").strip()]
    if manquantes:
        raise ImproperlyConfigured(
            "Configuration R2 incomplète, variables manquantes : " + ", ".join(manquantes)
        )
    valeurs = {nom: env[nom].strip() for nom in VARIABLES_R2}

    endpoint = valeurs["AWS_S3_ENDPOINT_URL"].rstrip("/")
    # Le tableau de bord Cloudflare affiche « S3 API » avec le nom du bucket à la fin :
    # copié tel quel, il ferait chercher les fichiers dans <bucket>/<bucket>/...
    if not endpoint.startswith("https://") or endpoint.count("/") > 2:
        raise ImproperlyConfigured(
            "AWS_S3_ENDPOINT_URL doit être de la forme "
            "https://<ACCOUNT_ID>.r2.cloudflarestorage.com, sans nom de bucket."
        )
    domaine = valeurs["AWS_S3_CUSTOM_DOMAIN"]
    if "://" in domaine or "/" in domaine:
        raise ImproperlyConfigured(
            "AWS_S3_CUSTOM_DOMAIN doit être un nom de domaine seul, "
            "ex. media.wmbranhamtabernacle.org (sans https:// ni /)."
        )

    from botocore.config import Config

    return {
        "access_key": valeurs["AWS_ACCESS_KEY_ID"],
        "secret_key": valeurs["AWS_SECRET_ACCESS_KEY"],
        "bucket_name": valeurs["AWS_STORAGE_BUCKET_NAME"],
        "endpoint_url": endpoint,
        "region_name": "auto",
        "custom_domain": domaine,
        "url_protocol": "https:",
        # Contenu public : URLs stables, sans signature ni date d'expiration.
        "querystring_auth": False,
        "file_overwrite": False,
        # R2 ne gère pas les ACL : on n'en envoie aucune.
        "default_acl": None,
        "object_parameters": {"CacheControl": CACHE_CONTROL},
        # Les sommes de contrôle ajoutées par défaut dans les boto3 récents ne sont
        # pas toutes acceptées par R2 : on ne les envoie que lorsqu'elles sont requises.
        "client_config": Config(
            signature_version="s3v4",
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    }


def config_stockage(env):
    """Valeur du réglage STORAGES de Django pour l'environnement donné."""
    choix = (env.get("MEDIA_STORAGE") or "disque").strip().lower()
    if choix == "disque":
        default = DISQUE
    elif choix == "r2":
        default = {"BACKEND": BACKEND_R2, "OPTIONS": options_r2(env)}
    else:
        raise ImproperlyConfigured(f"MEDIA_STORAGE inconnu : {choix!r} (attendu : disque ou r2)")
    return {"default": default, "staticfiles": STATICFILES}
