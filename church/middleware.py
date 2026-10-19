from django.http import HttpResponsePermanentRedirect

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
