import django_filters as df

from actualites.models import Article
from api.models import Suppression
from OurData.models import Ministre, Temoignages
from sermons.models import Orateur, Sermons, Theme

AIDE_SYNCHRO = (
    "Synchronisation incrémentale : contenus modifiés à partir de cette date (ISO 8601, ex. "
    "2026-10-19T17:02:11Z ; encoder « + » en %2B). Comparaison inclusive : dédoublonner par id. "
    "Les résultats sont alors triés par date de modification croissante."
)


class FiltreSynchro(df.FilterSet):
    updated_since = df.IsoDateTimeFilter(field_name="date_modification", lookup_expr="gte", help_text=AIDE_SYNCHRO)


class FiltreSermons(FiltreSynchro):
    orateur = df.NumberFilter(field_name="orateur_id", help_text="Identifiant de l'orateur.")
    theme = df.NumberFilter(field_name="Theme_id", help_text="Identifiant du thème.")
    date_min = df.DateFilter(field_name="date", lookup_expr="date__gte", help_text="Prêché ce jour ou après (AAAA-MM-JJ).")
    date_max = df.DateFilter(field_name="date", lookup_expr="date__lte", help_text="Prêché ce jour ou avant (AAAA-MM-JJ).")
    q = df.CharFilter(field_name="titre", lookup_expr="icontains", help_text="Recherche dans le titre.")

    class Meta:
        model = Sermons
        fields = []


class FiltreThemes(FiltreSynchro):
    class Meta:
        model = Theme
        fields = []


class FiltreOrateurs(FiltreSynchro):
    class Meta:
        model = Orateur
        fields = []


class FiltreMinistres(FiltreSynchro):
    fonction = df.ChoiceFilter(choices=Ministre.FONCTION_CHOICES)

    class Meta:
        model = Ministre
        fields = []


class FiltreArticles(FiltreSynchro):
    categorie = df.CharFilter(field_name="categorie__slug", help_text="Slug de la catégorie.")
    en_vedette = df.BooleanFilter()
    q = df.CharFilter(field_name="titre", lookup_expr="icontains", help_text="Recherche dans le titre.")

    class Meta:
        model = Article
        fields = []


class FiltreTemoignages(FiltreSynchro):
    class Meta:
        model = Temoignages
        fields = []


class FiltreSuppressions(df.FilterSet):
    updated_since = df.IsoDateTimeFilter(
        field_name="date", lookup_expr="gte",
        help_text="Contenus disparus à partir de cette date (même format que pour les listes).",
    )

    class Meta:
        model = Suppression
        fields = []
