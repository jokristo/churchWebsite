from django.core.files.storage import FileSystemStorage, storages
from django.http import HttpResponsePermanentRedirect
from django.views.static import serve


def servir_media(request, path):
    """/media/<chemin> : sert le fichier depuis le disque, ou redirige vers R2.

    - Stockage disque (développement, ou production avant la bascule) : le fichier
      est servi par Django, que DEBUG soit activé ou non.
    - Stockage R2 : redirection permanente vers le domaine des médias, pour que les
      anciens liens (partagés sur WhatsApp, mis en cache par une app) restent valides.

    Le choix est fait à chaque requête, d'après le stockage réellement configuré.
    """
    stockage = storages["default"]
    if isinstance(stockage, FileSystemStorage):
        return serve(request, path, document_root=stockage.location)
    return HttpResponsePermanentRedirect(stockage.url(path))
