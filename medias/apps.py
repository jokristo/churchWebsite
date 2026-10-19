from django.apps import AppConfig


class MediasConfig(AppConfig):
    """Service des médias et migration entre le disque et Cloudflare R2 (voir church/stockage.py)."""
    name = 'medias'
    verbose_name = 'Médias'
