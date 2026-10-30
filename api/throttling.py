from django.conf import settings
from rest_framework.throttling import AnonRateThrottle


class LimiteAnonymes(AnonRateThrottle):
    """Plafond de requêtes par adresse IP pour les anonymes (API_LIMITE_ANONYMES).

    Derrière Cloudflare puis Render, REMOTE_ADDR est l'adresse d'un proxy : sans
    correction, tous les utilisateurs partageraient le même compteur. Cloudflare
    transmet l'adresse réelle du visiteur dans CF-Connecting-IP.

    Limite connue : un client qui contourne Cloudflare (adresse .onrender.com) peut
    falsifier cet en-tête pour échapper au plafond. Ce n'est pas une faille d'accès
    (l'API est publique et en lecture seule), seulement un contournement du plafond.
    """

    def get_rate(self):
        return getattr(settings, "API_LIMITE_ANONYMES", "120/min")

    def get_ident(self, request):
        return request.META.get("HTTP_CF_CONNECTING_IP") or super().get_ident(request)
