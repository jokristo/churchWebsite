"""Vues de l'API v1 : lecture seule, anonyme, réponses cachables (Cache-Control + ETag)."""
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils.cache import patch_cache_control
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from actualites.models import Article, Categorie
from api import filters, serializers
from api.models import Suppression
from OurData.models import Ministre, Temoignages
from sermons.models import Orateur, Sermons, Theme


class CacheMixin:
    """Contenu public, identique pour tous : cache court côté application (et Cloudflare
    s'il est configuré pour /api/). L'ETag est ajouté par church.middleware.

    Attention pour l'authentification future : une réponse personnalisée ne doit JAMAIS
    hériter de ce mixin (elle serait servie à d'autres utilisateurs) ; elle sera private."""

    duree_cache = 300

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if request.method in ("GET", "HEAD") and response.status_code == 200:
            patch_cache_control(response, public=True, max_age=self.duree_cache)
        response["X-Robots-Tag"] = "noindex"
        return response


class LectureViewSet(CacheMixin, viewsets.ReadOnlyModelViewSet):
    ordre = None
    ordre_synchro = ("date_modification", "id")


class SermonViewSet(LectureViewSet):
    """Prédications, des plus récentes aux plus anciennes."""

    # date peut être vide : on se rabat sur la date de modification pour un tri stable.
    queryset = Sermons.objects.select_related("orateur", "Theme").annotate(
        date_tri=Coalesce(F("date"), F("date_modification"))
    )
    serializer_class = serializers.SermonSerializer
    filterset_class = filters.FiltreSermons
    ordre = ("-date_tri", "-id")


class ThemeViewSet(LectureViewSet):
    queryset = Theme.objects.all()
    serializer_class = serializers.ThemeSerializer
    filterset_class = filters.FiltreThemes
    ordre = ("NomTheme", "id")


class OrateurViewSet(LectureViewSet):
    queryset = Orateur.objects.all()
    serializer_class = serializers.OrateurSerializer
    filterset_class = filters.FiltreOrateurs
    ordre = ("Noms", "id")


class MinistreViewSet(LectureViewSet):
    queryset = Ministre.objects.all()
    serializer_class = serializers.MinistreSerializer
    filterset_class = filters.FiltreMinistres
    ordre = ("ordre", "Nom", "id")


class CategorieViewSet(LectureViewSet):
    """Catégories des articles (liste courte, sans synchronisation incrémentale)."""

    queryset = Categorie.objects.all()
    serializer_class = serializers.CategorieSerializer
    ordre = ("nom", "id")
    ordre_synchro = None


class ArticleViewSet(LectureViewSet):
    """Articles publiés uniquement ; le détail se lit par slug."""

    queryset = Article.objects.filter(est_publie=True).select_related("categorie")
    filterset_class = filters.FiltreArticles
    lookup_field = "slug"
    ordre = ("-date_publication", "-id")

    def get_serializer_class(self):
        return serializers.ArticleDetailSerializer if self.action == "retrieve" else serializers.ArticleSerializer


class TemoignageViewSet(LectureViewSet):
    """Témoignages approuvés uniquement."""

    queryset = Temoignages.objects.filter(is_Approuve=True)
    serializer_class = serializers.TemoignageSerializer
    filterset_class = filters.FiltreTemoignages
    ordre = ("-id",)


class SuppressionListView(CacheMixin, generics.ListAPIView):
    """Contenus disparus de l'API (supprimés, dépubliés, désapprouvés) : à retirer du
    stockage hors ligne de l'application. Un contenu retiré puis republié réapparaît
    dans sa liste avec une date_modification plus récente."""

    queryset = Suppression.objects.all()
    serializer_class = serializers.SuppressionSerializer
    filterset_class = filters.FiltreSuppressions
    ordre = ("date", "id")
    ordre_synchro = ("date", "id")


class EgliseView(CacheMixin, APIView):
    """Informations de l'église, lues depuis church/seo.py (les mêmes que sur le site)."""

    duree_cache = 3600

    @extend_schema(responses=serializers.EgliseSerializer)
    def get(self, request):
        return Response(serializers.EgliseSerializer(serializers.donnees_eglise()).data)


class SchemaView(CacheMixin, SpectacularAPIView):
    duree_cache = 3600


class DocumentationView(CacheMixin, SpectacularSwaggerView):
    duree_cache = 3600
