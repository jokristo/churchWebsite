import mimetypes

from storages.backends.s3 import S3Storage

import church.stockage  # noqa: F401 — enregistre les types MIME (.webp, .mp3, .m4a)


class StockageR2(S3Storage):
    """S3Storage pour Cloudflare R2, avec un Content-Type fiable.

    Par défaut, django-storages préfère le type annoncé par le navigateur lors de
    l'upload (parfois audio/x-m4a ou application/octet-stream), ce qui peut empêcher
    la lecture sur Safari. On impose le type déduit de l'extension quand il est connu
    (voir les types déclarés dans church/stockage.py).
    """

    def get_object_parameters(self, name):
        parametres = super().get_object_parameters(name)
        type_mime, _ = mimetypes.guess_type(name)
        if type_mime:
            parametres["ContentType"] = type_mime
        return parametres
