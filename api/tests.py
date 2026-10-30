"""API v1 de l'application mobile : forme des réponses, filtres, pagination, exclusions,
synchronisation incrémentale, cache, plafond de requêtes et schéma OpenAPI."""
import tempfile
from datetime import datetime, timedelta, timezone as tz
from urllib.parse import urlsplit

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from actualites.models import Article, Categorie
from api.models import Suppression
from church import seo
from church.stockage import config_stockage
from church.utils import audio
from OurData.models import Ministre, Temoignages
from sermons.models import Orateur, Sermons, Theme

ENV_R2 = {
    "MEDIA_STORAGE": "r2", "AWS_ACCESS_KEY_ID": "cle", "AWS_SECRET_ACCESS_KEY": "secret",
    "AWS_STORAGE_BUCKET_NAME": "wmbtab-media",
    "AWS_S3_ENDPOINT_URL": "https://0123456789abcdef0123456789abcdef.r2.cloudflarestorage.com",
    "AWS_S3_CUSTOM_DOMAIN": "media.wmbranhamtabernacle.org",
}
KINSHASA = tz(timedelta(hours=1))


def kin(*args):
    return datetime(*args, tzinfo=KINSHASA)


class BaseApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ministre = Ministre.objects.create(Nom="Bob Munanga Matekya", fonction="titulaire", ordre=1,
                                               contact="+243000000000", photo="ministrespictures/bob.webp")
        cls.ministre2 = Ministre.objects.create(Nom="Joseph Tshole Luzolo", fonction="associe", ordre=2)
        cls.orateur = Orateur.objects.create(Noms="Bob Munanga", Provenance="Kinshasa", ministre=cls.ministre)
        cls.orateur2 = Orateur.objects.create(Noms="Joseph Tshole")
        cls.theme = Theme.objects.create(NomTheme="La grâce", ThemeDescription="d", ministre=cls.ministre,
                                         image="sermons/grace.webp")
        cls.theme2 = Theme.objects.create(NomTheme="La foi")
        cls.sermon = Sermons.objects.create(titre="La grâce souveraine", orateur=cls.orateur, Theme=cls.theme,
                                            date=kin(2026, 1, 10, 10, 30), audio="audio/grace-64k.mp3",
                                            image="sermons/grace.webp")
        Sermons.objects.filter(pk=cls.sermon.pk).update(audio_taille=33554432, audio_duree=4210)
        cls.sermon2 = Sermons.objects.create(titre="La foi qui vainc", orateur=cls.orateur2, Theme=cls.theme2,
                                             date=kin(2026, 3, 5, 17, 0))
        cls.sermon3 = Sermons.objects.create(titre="Grâce et vérité", orateur=cls.orateur, Theme=cls.theme2,
                                             date=kin(2025, 12, 1, 10, 30))
        cls.categorie = Categorie.objects.create(nom="Annonces")
        cls.article = Article.objects.create(titre="Culte de Pâques", slug="culte-de-paques", resume="Résumé",
                                             contenu="Premier paragraphe.\n\nSecond.", est_publie=True,
                                             en_vedette=True, categorie=cls.categorie)
        cls.article2 = Article.objects.create(titre="Veillée de prière", slug="veillee", resume="r", contenu="c",
                                              est_publie=True)
        cls.brouillon = Article.objects.create(titre="Brouillon", slug="brouillon", resume="r", contenu="c",
                                               est_publie=False)
        cls.temoignage = Temoignages.objects.create(NomDuCroyant="Marie", Description="Guérie", is_Approuve=True)
        cls.temoignage_en_attente = Temoignages.objects.create(NomDuCroyant="Paul", Description="?", is_Approuve=False)

    def setUp(self):
        cache.clear()  # compteurs du plafond de requêtes

    def get(self, url, **kwargs):
        reponse = self.client.get(f"/api/v1/{url}", **kwargs)
        return reponse

    def resultats(self, url):
        reponse = self.get(url)
        self.assertEqual(reponse.status_code, 200, reponse.content)
        return reponse.json()["results"]

    def ids(self, url):
        return [r["id"] for r in self.resultats(url)]


class FormeReponsesTests(BaseApiTests):
    def test_sermon(self):
        donnees = self.get(f"sermons/{self.sermon.pk}/").json()
        modification = donnees.pop("date_modification")
        self.assertEqual(donnees, {
            "id": self.sermon.pk,
            "titre": "La grâce souveraine",
            "date": "2026-01-10T10:30:00+01:00",
            "orateur": {"id": self.orateur.pk, "nom": "Bob Munanga"},
            "theme": {"id": self.theme.pk, "nom": "La grâce"},
            "image_url": "http://testserver/media/sermons/grace.webp",
            "audio": {"url": "http://testserver/media/audio/grace-64k.mp3", "taille_octets": 33554432,
                      "duree_secondes": 4210, "type_mime": "audio/mpeg"},
            "lien": None,
        })
        self.assertTrue(datetime.fromisoformat(modification).tzinfo)

    def test_sermon_sans_audio_ni_image(self):
        donnees = self.get(f"sermons/{self.sermon2.pk}/").json()
        self.assertIsNone(donnees["audio"])
        self.assertIsNone(donnees["image_url"])

    def test_listes_simples(self):
        attendus = {
            "themes/": {"id", "nom", "description", "image_url", "ministre_id", "date_modification"},
            "orateurs/": {"id", "nom", "provenance", "ministre_id", "date_modification"},
            "ministres/": {"id", "nom", "fonction", "fonction_libelle", "photo_url", "ordre", "date_modification"},
            "categories/": {"id", "slug", "nom"},
            "articles/": {"id", "slug", "titre", "resume", "categorie", "image_url", "date_publication",
                          "date_evenement", "en_vedette", "date_modification"},
            "temoignages/": {"id", "nom_croyant", "description", "photo_url", "audio", "date_modification"},
        }
        for url, champs in attendus.items():
            with self.subTest(url=url):
                self.assertEqual(set(self.resultats(url)[0]), champs)

    def test_valeurs_traduites_depuis_les_modeles(self):
        theme = next(t for t in self.resultats("themes/") if t["id"] == self.theme.pk)
        self.assertEqual((theme["nom"], theme["ministre_id"]), ("La grâce", self.ministre.pk))
        orateur = next(o for o in self.resultats("orateurs/") if o["id"] == self.orateur.pk)
        self.assertEqual((orateur["nom"], orateur["provenance"]), ("Bob Munanga", "Kinshasa"))
        ministre = self.resultats("ministres/")[0]
        self.assertEqual((ministre["nom"], ministre["fonction"], ministre["fonction_libelle"]),
                         ("Bob Munanga Matekya", "titulaire", "Pasteur titulaire"))
        self.assertEqual(ministre["photo_url"], "http://testserver/media/ministrespictures/bob.webp")
        temoignage = self.resultats("temoignages/")[0]
        self.assertEqual((temoignage["nom_croyant"], temoignage["description"]), ("Marie", "Guérie"))

    def test_telephone_des_ministres_non_expose(self):
        self.assertNotIn("+243000000000", self.get("ministres/").content.decode())

    def test_article_liste_et_detail(self):
        liste = next(a for a in self.resultats("articles/") if a["slug"] == "culte-de-paques")
        self.assertNotIn("contenu", liste)
        self.assertEqual(liste["categorie"], {"slug": "annonces", "nom": "Annonces"})
        detail = self.get("articles/culte-de-paques/").json()
        self.assertEqual(detail["contenu"], "Premier paragraphe.\n\nSecond.")
        self.assertNotIn("auteur", detail)

    def test_eglise_lue_depuis_seo(self):
        donnees = self.get("eglise/").json()
        self.assertEqual(donnees["nom"], seo.EGLISE["nom"])
        self.assertEqual(donnees["adresse"], seo.EGLISE["adresse"])
        self.assertEqual(donnees["telephone"], seo.EGLISE["telephone"])
        self.assertEqual(donnees["whatsapp_url"], seo.EGLISE["whatsapp"])
        self.assertEqual(donnees["maps_url"], seo.maps_search_url())
        self.assertEqual(donnees["fuseau_horaire"], "Africa/Kinshasa")
        self.assertIn({"jour": "Dimanche", "jour_semaine": 7, "debut": "10:30", "fin": None,
                       "libelle": "à partir de 10h30"}, donnees["horaires"])
        self.assertTrue(donnees["logo_url"].startswith("https://www.wmbranhamtabernacle.org/static/"))

    def test_urls_absolues_sur_r2(self):
        with self.settings(STORAGES=config_stockage(ENV_R2)):
            donnees = self.get(f"sermons/{self.sermon.pk}/").json()
        self.assertEqual(donnees["image_url"], "https://media.wmbranhamtabernacle.org/sermons/grace.webp")
        self.assertEqual(donnees["audio"]["url"], "https://media.wmbranhamtabernacle.org/audio/grace-64k.mp3")


class ExclusionsTests(BaseApiTests):
    def test_articles_non_publies_exclus(self):
        self.assertNotIn("brouillon", [a["slug"] for a in self.resultats("articles/")])
        self.assertEqual(self.get("articles/brouillon/").status_code, 404)

    def test_temoignages_non_approuves_exclus(self):
        self.assertEqual(self.ids("temoignages/"), [self.temoignage.pk])
        self.assertEqual(self.get(f"temoignages/{self.temoignage_en_attente.pk}/").status_code, 404)


class FiltresTests(BaseApiTests):
    def test_sermons(self):
        cas = {
            f"sermons/?orateur={self.orateur.pk}": {self.sermon.pk, self.sermon3.pk},
            f"sermons/?theme={self.theme2.pk}": {self.sermon2.pk, self.sermon3.pk},
            "sermons/?date_min=2026-01-01": {self.sermon.pk, self.sermon2.pk},
            "sermons/?date_max=2026-01-10": {self.sermon.pk, self.sermon3.pk},
            "sermons/?date_min=2026-01-01&date_max=2026-01-31": {self.sermon.pk},
            "sermons/?q=grâce": {self.sermon.pk, self.sermon3.pk},
            # Casse ignorée (les accents, eux, comptent : « grace » ne trouve pas « grâce »)
            f"sermons/?q=LA GRâce&orateur={self.orateur.pk}&theme={self.theme.pk}": {self.sermon.pk},
        }
        for url, attendus in cas.items():
            with self.subTest(url=url):
                self.assertEqual(set(self.ids(url)), attendus)

    def test_sermons_tries_du_plus_recent_au_plus_ancien(self):
        self.assertEqual(self.ids("sermons/"), [self.sermon2.pk, self.sermon.pk, self.sermon3.pk])

    def test_articles_et_ministres(self):
        self.assertEqual([a["slug"] for a in self.resultats("articles/?categorie=annonces")], ["culte-de-paques"])
        self.assertEqual([a["slug"] for a in self.resultats("articles/?en_vedette=true")], ["culte-de-paques"])
        self.assertEqual([a["slug"] for a in self.resultats("articles/?q=veillée")], ["veillee"])
        self.assertEqual(self.ids("ministres/?fonction=associe"), [self.ministre2.pk])

    def test_valeur_invalide_refusee(self):
        for url in ["sermons/?date_min=hier", "sermons/?orateur=abc", "sermons/?updated_since=pas-une-date",
                    "ministres/?fonction=pape"]:
            with self.subTest(url=url):
                self.assertEqual(self.get(url).status_code, 400)


class PaginationTests(BaseApiTests):
    def test_curseur_sans_doublon_ni_oubli(self):
        premiere = self.get("sermons/?taille=2").json()
        self.assertEqual(len(premiere["results"]), 2)
        self.assertIsNone(premiere["previous"])
        suivante = urlsplit(premiere["next"])
        self.assertEqual(suivante.netloc, "testserver")  # lien absolu
        seconde = self.client.get(f"{suivante.path}?{suivante.query}").json()
        self.assertIsNone(seconde["next"])
        self.assertIsNotNone(seconde["previous"])
        tous = [s["id"] for s in premiere["results"] + seconde["results"]]
        self.assertEqual(tous, [self.sermon2.pk, self.sermon.pk, self.sermon3.pk])

    def test_taille_par_defaut_et_maximum(self):
        for i in range(25):
            Sermons.objects.create(titre=f"Sermon {i}", date=kin(2024, 1, 1) + timedelta(days=i))
        self.assertEqual(len(self.resultats("sermons/")), 20)
        self.assertEqual(len(self.resultats("sermons/?taille=500")), 28)  # plafond 100, 28 sermons au total

    def test_sermon_sans_date_reste_paginable(self):
        Sermons.objects.filter(pk=self.sermon3.pk).update(date=None)
        self.assertEqual(set(self.ids("sermons/?taille=100")), {self.sermon.pk, self.sermon2.pk, self.sermon3.pk})


class SynchronisationTests(BaseApiTests):
    def dater(self, objet, quand):
        type(objet).objects.filter(pk=objet.pk).update(date_modification=quand)

    def test_updated_since_et_ordre_croissant(self):
        for s, quand in [(self.sermon, kin(2026, 1, 1)), (self.sermon2, kin(2026, 5, 2)), (self.sermon3, kin(2026, 5, 1))]:
            self.dater(s, quand)
        self.assertEqual(self.ids("sermons/?updated_since=2026-04-30T00:00:00Z"), [self.sermon3.pk, self.sermon2.pk])
        self.assertEqual(self.ids("sermons/?updated_since=2026-05-02T00:00:00%2B01:00"), [self.sermon2.pk])

    def test_updated_since_sur_chaque_liste(self):
        futur = timezone.now() + timedelta(days=1)
        for url in ["sermons/", "themes/", "orateurs/", "ministres/", "articles/", "temoignages/"]:
            with self.subTest(url=url):
                self.assertEqual(self.resultats(f"{url}?updated_since={futur.isoformat().replace('+', '%2B')}"), [])

    def test_suppression_depublication_desapprobation(self):
        avant = timezone.now() - timedelta(seconds=1)
        sermon_pk = self.sermon3.pk
        self.sermon3.delete()
        self.article2.est_publie = False
        self.article2.save()
        self.temoignage.is_Approuve = False
        self.temoignage.save()
        self.brouillon.titre = "Toujours brouillon"
        self.brouillon.save()  # jamais publié : aucune trace
        suppressions = self.resultats(f"suppressions/?updated_since={avant.isoformat().replace('+', '%2B')}")
        self.assertEqual(
            [(s["type"], s["id"], s["motif"]) for s in suppressions],
            [("sermon", sermon_pk, "supprime"), ("article", self.article2.pk, "depublie"),
             ("temoignage", self.temoignage.pk, "desapprouve")],
        )
        self.assertEqual(set(suppressions[0]), {"type", "id", "motif", "date"})

    def test_republication_visible_par_updated_since(self):
        self.article2.est_publie = False
        self.article2.save()
        avant = timezone.now()
        self.article2.est_publie = True
        self.article2.save()
        self.assertIn("veillee", [a["slug"] for a in self.resultats(
            f"articles/?updated_since={avant.isoformat().replace('+', '%2B')}")])

    def test_renommer_un_orateur_redate_ses_sermons(self):
        self.dater(self.sermon, kin(2020, 1, 1))
        self.dater(self.sermon2, kin(2020, 1, 1))
        avant = timezone.now()
        self.orateur.Noms = "Pasteur Bob Munanga"
        self.orateur.save()
        modifies = self.resultats(f"sermons/?updated_since={avant.isoformat().replace('+', '%2B')}")
        self.assertIn(self.sermon.pk, [s["id"] for s in modifies])
        self.assertNotIn(self.sermon2.pk, [s["id"] for s in modifies])
        self.assertEqual(next(s for s in modifies if s["id"] == self.sermon.pk)["orateur"]["nom"], "Pasteur Bob Munanga")

    def test_supprimer_un_theme_redate_ses_sermons(self):
        self.dater(self.sermon, kin(2020, 1, 1))
        avant = timezone.now()
        self.theme.delete()
        modifies = self.resultats(f"sermons/?updated_since={avant.isoformat().replace('+', '%2B')}")
        sermon = next(s for s in modifies if s["id"] == self.sermon.pk)
        self.assertIsNone(sermon["theme"])

    def test_traitement_audio_redate_le_sermon(self):
        # Les fins de traitement audio passent par queryset.update(), qui ignore auto_now
        self.dater(self.sermon, kin(2020, 1, 1))
        avant = timezone.now()
        Sermons.objects.filter(pk=self.sermon.pk).update(audio_etat=audio.EN_COURS)
        audio._terminer(Sermons, self.sermon.pk, "audio/grace-64k.mp3", audio.IGNORE, "déjà léger",
                        audio_taille=1234, audio_duree=60)
        modifies = self.resultats(f"sermons/?updated_since={avant.isoformat().replace('+', '%2B')}")
        self.assertEqual(modifies[0]["audio"]["taille_octets"], 1234)


class CacheTests(BaseApiTests):
    def test_entetes(self):
        for url, duree in [("sermons/", 300), (f"sermons/{self.sermon.pk}/", 300), ("eglise/", 3600)]:
            with self.subTest(url=url):
                reponse = self.get(url)
                self.assertEqual(reponse["Cache-Control"], f"public, max-age={duree}")
                self.assertEqual(reponse["X-Robots-Tag"], "noindex")
                self.assertTrue(reponse.has_header("ETag"))

    def test_304_si_rien_n_a_change(self):
        etag = self.get("sermons/")["ETag"]
        reponse = self.get("sermons/", HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(reponse.status_code, 304)
        self.assertEqual(reponse.content, b"")
        Sermons.objects.filter(pk=self.sermon.pk).update(titre="Nouveau titre")
        self.assertEqual(self.get("sermons/", HTTP_IF_NONE_MATCH=etag).status_code, 200)

    def test_pas_d_etag_sur_les_pages_du_site(self):
        self.assertFalse(self.client.get("/").has_header("ETag"))

    def test_api_exclue_des_moteurs(self):
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /api/")


class SecuriteTests(BaseApiTests):
    def test_lecture_seule(self):
        for methode, url in [("post", "sermons/"), ("put", f"sermons/{self.sermon.pk}/"),
                             ("patch", f"sermons/{self.sermon.pk}/"), ("delete", f"sermons/{self.sermon.pk}/"),
                             ("post", "eglise/"), ("delete", "suppressions/")]:
            with self.subTest(methode=methode, url=url):
                self.assertEqual(getattr(self.client, methode)(f"/api/v1/{url}").status_code, 405)
        self.assertTrue(Sermons.objects.filter(pk=self.sermon.pk).exists())

    @override_settings(API_LIMITE_ANONYMES="3/min")
    def test_plafond_par_visiteur_reel(self):
        for _ in range(3):
            self.assertEqual(self.get("themes/", HTTP_CF_CONNECTING_IP="41.243.0.1").status_code, 200)
        bloque = self.get("themes/", HTTP_CF_CONNECTING_IP="41.243.0.1")
        self.assertEqual(bloque.status_code, 429)
        self.assertTrue(bloque.has_header("Retry-After"))
        # Un autre abonné derrière le même proxy Cloudflare garde son propre compteur
        self.assertEqual(self.get("themes/", HTTP_CF_CONNECTING_IP="41.243.0.2").status_code, 200)

    def test_json_uniquement(self):
        reponse = self.get("sermons/", HTTP_ACCEPT="text/html")
        self.assertEqual(reponse.status_code, 406)


class SchemaTests(BaseApiTests):
    def test_schema_valide_sans_avertissement(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml") as fichier:
            call_command("spectacular", "--validate", "--fail-on-warn", "--file", fichier.name)

    def test_schema_et_documentation_servis(self):
        self.assertEqual(self.get("schema/").status_code, 200)
        self.assertContains(self.get("docs/"), "swagger")
