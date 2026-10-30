from django.apps import AppConfig


class ApiConfig(AppConfig):
    """API REST v1 pour l'application mobile (voir CLAUDE.md, « Application mobile et API »)."""
    name = 'api'
    verbose_name = 'API mobile'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from api import signals  # noqa: F401 — enregistre les suppressions et les dates
