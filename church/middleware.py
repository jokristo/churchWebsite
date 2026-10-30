from django.http import HttpResponsePermanentRedirect
from django.middleware.http import ConditionalGetMiddleware

DOMAINE_OFFICIEL = "www.wmbranhamtabernacle.org"
DOMAINE_SANS_WWW = "wmbranhamtabernacle.org"


class DomaineCanoniqueMiddleware:
    """
    - Redirige wmbranhamtabernacle.org -> www.wmbranhamtabernacle.org (301),
      pour que Google ne voie qu'une seule version du site.
    - Demande aux moteurs de ne pas indexer l'adresse technique *.onrender.com
      (sinon le site existe en double dans Google).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hote = request.get_host().split(":")[0].lower()
        if hote == DOMAINE_SANS_WWW:
            return HttpResponsePermanentRedirect(
                f"https://{DOMAINE_OFFICIEL}{request.get_full_path()}"
            )
        response = self.get_response(request)
        if hote.endswith(".onrender.com"):
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response


class ConditionalGetApiMiddleware(ConditionalGetMiddleware):
    """ETag et réponses 304 pour l'API uniquement.

    L'application renvoie l'ETag reçu (If-None-Match) : si rien n'a changé, le serveur
    répond 304 sans contenu, ce qui économise les données mobiles. Limité à /api/ pour
    ne pas modifier le comportement des pages du site.
    """

    def process_response(self, request, response):
        if not request.path.startswith("/api/"):
            return response
        return super().process_response(request, response)
