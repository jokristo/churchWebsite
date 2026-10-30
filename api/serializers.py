"""Serializers de l'API v1 : noms de champs en français et en snake_case, quels que soient
les noms des modèles (Noms, NomTheme, Theme, is_Approuve…). Ces noms sont un contrat avec
l'application mobile : un renommage ou un retrait impose /api/v2/ (ajouter un champ est permis).
"""
import mimetypes

from django.conf import settings
from django.templatetags.static import static
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from actualites.models import Article, Categorie
from api.models import Suppression
from church import seo
from OurData.models import Ministre, Temoignages
from sermons.models import Orateur, Sermons, Theme


def url_absolue(request, fichier):
    """URL absolue d'un média : déjà absolue sur R2, à compléter en stockage disque."""
    if not fichier:
        return None
    url = fichier.url
    return url if url.startswith(("http://", "https://")) else request.build_absolute_uri(url)


class ChampMedia(serializers.Field):
    """URL absolue d'un fichier ou d'une image (null si absent)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return getattr(instance, self.source)

    def to_representation(self, fichier):
        return url_absolue(self.context["request"], fichier)


extend_schema_field({"type": "string", "format": "uri", "nullable": True})(ChampMedia)


class AudioSerializer(serializers.Serializer):
    """Ce dont le lecteur et le téléchargement hors ligne ont besoin."""

    url = serializers.URLField()
    taille_octets = serializers.IntegerField(allow_null=True, help_text="Taille du fichier, null tant qu'elle n'est pas mesurée.")
    duree_secondes = serializers.IntegerField(allow_null=True, help_text="Durée, null tant qu'elle n'est pas mesurée.")
    type_mime = serializers.CharField()


def representer_audio(serializer, instance, champ):
    fichier = getattr(instance, champ)
    if not fichier:
        return None
    return {
        "url": url_absolue(serializer.context["request"], fichier),
        "taille_octets": instance.audio_taille,
        "duree_secondes": instance.audio_duree,
        "type_mime": mimetypes.guess_type(fichier.name)[0] or "application/octet-stream",
    }


class ReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom = serializers.CharField()


# --- Prédications ---

class SermonSerializer(serializers.ModelSerializer):
    orateur = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    image_url = ChampMedia(source="image")
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Sermons
        fields = ["id", "titre", "date", "orateur", "theme", "image_url", "audio", "lien", "date_modification"]

    @extend_schema_field(ReferenceSerializer(allow_null=True))
    def get_orateur(self, sermon):
        o = sermon.orateur
        return {"id": o.id, "nom": o.Noms} if o else None

    @extend_schema_field(ReferenceSerializer(allow_null=True))
    def get_theme(self, sermon):
        t = sermon.Theme
        return {"id": t.id, "nom": t.NomTheme} if t else None

    @extend_schema_field(AudioSerializer(allow_null=True))
    def get_audio(self, sermon):
        return representer_audio(self, sermon, "audio")


class ThemeSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source="NomTheme")
    description = serializers.CharField(source="ThemeDescription", allow_null=True)
    image_url = ChampMedia(source="image")
    ministre_id = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Theme
        fields = ["id", "nom", "description", "image_url", "ministre_id", "date_modification"]


class OrateurSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source="Noms")
    provenance = serializers.CharField(source="Provenance", allow_null=True)
    ministre_id = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Orateur
        fields = ["id", "nom", "provenance", "ministre_id", "date_modification"]


class MinistreSerializer(serializers.ModelSerializer):
    """Sans le téléphone : on pourra l'ajouter plus tard, le retirer serait incompatible."""

    nom = serializers.CharField(source="Nom")
    fonction_libelle = serializers.CharField(source="get_fonction_display")
    photo_url = ChampMedia(source="photo")

    class Meta:
        model = Ministre
        fields = ["id", "nom", "fonction", "fonction_libelle", "photo_url", "ordre", "date_modification"]


# --- Actualités ---

class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ["id", "slug", "nom"]


class CategorieReferenceSerializer(serializers.Serializer):
    slug = serializers.CharField()
    nom = serializers.CharField()


class ArticleSerializer(serializers.ModelSerializer):
    categorie = serializers.SerializerMethodField()
    image_url = ChampMedia(source="image_couverture")

    class Meta:
        model = Article
        fields = ["id", "slug", "titre", "resume", "categorie", "image_url", "date_publication",
                  "date_evenement", "en_vedette", "date_modification"]

    @extend_schema_field(CategorieReferenceSerializer(allow_null=True))
    def get_categorie(self, article):
        c = article.categorie
        return {"slug": c.slug, "nom": c.nom} if c else None


class ArticleDetailSerializer(ArticleSerializer):
    contenu = serializers.CharField(help_text="Texte brut ; les paragraphes sont séparés par une ligne vide.")

    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields + ["contenu"]


# --- Témoignages ---

class TemoignageSerializer(serializers.ModelSerializer):
    nom_croyant = serializers.CharField(source="NomDuCroyant")
    description = serializers.CharField(source="Description")
    photo_url = ChampMedia(source="photo")
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Temoignages
        fields = ["id", "nom_croyant", "description", "photo_url", "audio", "date_modification"]

    @extend_schema_field(AudioSerializer(allow_null=True))
    def get_audio(self, temoignage):
        return representer_audio(self, temoignage, "Audio")


# --- Synchronisation ---

class SuppressionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="objet_id", help_text="Identifiant du contenu disparu.")

    class Meta:
        model = Suppression
        fields = ["type", "id", "motif", "date"]


# --- Église (données de church/seo.py) ---

class AdresseSerializer(serializers.Serializer):
    rue = serializers.CharField()
    commune = serializers.CharField()
    ville = serializers.CharField()
    pays = serializers.CharField(help_text="Code pays ISO 3166-1 (CD).")
    repere = serializers.CharField()


class HoraireSerializer(serializers.Serializer):
    jour = serializers.CharField(help_text="En français : Mercredi, Dimanche…")
    jour_semaine = serializers.IntegerField(help_text="1 = lundi … 7 = dimanche (ISO 8601).")
    debut = serializers.CharField(help_text="Heure locale de Kinshasa, HH:MM.")
    fin = serializers.CharField(allow_null=True)
    libelle = serializers.CharField(help_text="Exemple : « à partir de 17h ».")


class CoordonneesSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class EgliseSerializer(serializers.Serializer):
    nom = serializers.CharField()
    noms_alternatifs = serializers.ListField(child=serializers.CharField())
    description = serializers.CharField()
    adresse = AdresseSerializer()
    telephone = serializers.CharField()
    whatsapp_url = serializers.URLField()
    horaires = HoraireSerializer(many=True)
    coordonnees = CoordonneesSerializer(allow_null=True)
    maps_url = serializers.URLField()
    reseaux = serializers.ListField(child=serializers.URLField())
    site_url = serializers.URLField()
    logo_url = serializers.URLField()
    fuseau_horaire = serializers.CharField()


JOURS_ISO = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6, "Sunday": 7}


def donnees_eglise():
    e = seo.EGLISE
    libelles = seo.horaires_lisibles()
    coordonnees = None
    if e["latitude"] is not None and e["longitude"] is not None:
        coordonnees = {"latitude": e["latitude"], "longitude": e["longitude"]}
    return {
        "nom": e["nom"],
        "noms_alternatifs": e["noms_alternatifs"],
        "description": e["description"],
        "adresse": e["adresse"],
        "telephone": e["telephone"],
        "whatsapp_url": e["whatsapp"],
        "horaires": [
            {"jour": seo.JOURS_FR.get(jour, jour), "jour_semaine": JOURS_ISO[jour],
             "debut": debut, "fin": fin, "libelle": libelle["texte"]}
            for (jour, debut, fin), libelle in zip(e["horaires"], libelles)
        ],
        "coordonnees": coordonnees,
        "maps_url": seo.maps_search_url(),
        "reseaux": e["reseaux"],
        "site_url": seo.site_url() + "/",
        "logo_url": seo.url_absolue(static("logo24.png")),
        "fuseau_horaire": settings.TIME_ZONE,
    }
