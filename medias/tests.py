"""Stockage des médias : configuration, Cloudflare R2, service /media/, mixin audio, migration."""
import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage, storages
from django.core.management import call_command
from django.db.models.fields.files import FieldFile
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from church.stockage import CACHE_CONTROL, STATICFILES, config_stockage, options_r2

ENV_R2 = {
    "MEDIA_STORAGE": "r2",
    "AWS_ACCESS_KEY_ID": "cle-factice",
    "AWS_SECRET_ACCESS_KEY": "secret-factice",
    "AWS_STORAGE_BUCKET_NAME": "wmbtab-media",
    "AWS_S3_ENDPOINT_URL": "https://0123456789abcdef0123456789abcdef.r2.cloudflarestorage.com/",
    "AWS_S3_CUSTOM_DOMAIN": "media.wmbranhamtabernacle.org",
}
STOCKAGE_MEMOIRE = {"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}, "staticfiles": STATICFILES}


def stockages_disque(dossier):
    return {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage",
                        "OPTIONS": {"location": dossier}}, "staticfiles": STATICFILES}


class ConfigStockageTests(SimpleTestCase):
    def test_disque_par_defaut(self):
        self.assertEqual(config_stockage({})["default"]["BACKEND"], "django.core.files.storage.FileSystemStorage")
        self.assertEqual(config_stockage({})["staticfiles"], STATICFILES)

    def test_cles_presentes_sans_interrupteur_restent_sur_disque(self):
        # Un .env de développement qui contient les clés R2 ne doit pas écrire en production
        env = {k: v for k, v in ENV_R2.items() if k != "MEDIA_STORAGE"}
        self.assertEqual(config_stockage(env)["default"]["BACKEND"], "django.core.files.storage.FileSystemStorage")

    def test_r2(self):
        default = config_stockage(ENV_R2)["default"]
        self.assertEqual(default["BACKEND"], "medias.stockage.StockageR2")
        options = default["OPTIONS"]
        self.assertEqual(options["bucket_name"], "wmbtab-media")
        self.assertEqual(options["endpoint_url"], "https://0123456789abcdef0123456789abcdef.r2.cloudflarestorage.com")
        self.assertEqual(options["custom_domain"], "media.wmbranhamtabernacle.org")
        self.assertEqual(options["region_name"], "auto")
        self.assertFalse(options["querystring_auth"])
        self.assertFalse(options["file_overwrite"])
        self.assertIsNone(options["default_acl"])
        self.assertEqual(options["object_parameters"], {"CacheControl": CACHE_CONTROL})
        self.assertEqual(options["client_config"].request_checksum_calculation, "when_required")

    def test_variables_manquantes(self):
        env = dict(ENV_R2, AWS_SECRET_ACCESS_KEY="")
        with self.assertRaisesMessage(ImproperlyConfigured, "AWS_SECRET_ACCESS_KEY"):
            config_stockage(env)

    def test_endpoint_avec_nom_de_bucket_refuse(self):
        # Le tableau de bord Cloudflare affiche l'URL S3 suivie du nom du bucket
        env = dict(ENV_R2, AWS_S3_ENDPOINT_URL=ENV_R2["AWS_S3_ENDPOINT_URL"] + "wmbtab-media")
        with self.assertRaisesMessage(ImproperlyConfigured, "sans nom de bucket"):
            config_stockage(env)

    def test_domaine_avec_protocole_refuse(self):
        env = dict(ENV_R2, AWS_S3_CUSTOM_DOMAIN="https://media.wmbranhamtabernacle.org")
        with self.assertRaises(ImproperlyConfigured):
            config_stockage(env)

    def test_valeur_inconnue(self):
        with self.assertRaises(ImproperlyConfigured):
            config_stockage({"MEDIA_STORAGE": "s3"})


class StockageR2Tests(SimpleTestCase):
    """Sans réseau : construire une URL publique ou les paramètres d'envoi n'appelle pas R2."""

    def setUp(self):
        from medias.stockage import StockageR2
        self.stockage = StockageR2(**options_r2(ENV_R2))

    def test_url_publique_sans_signature(self):
        url = self.stockage.url("audio/Grâce souveraine.mp3")
        self.assertEqual(url, "https://media.wmbranhamtabernacle.org/audio/Gr%C3%A2ce%20souveraine.mp3")

    def test_entetes_a_l_envoi(self):
        cas = {
            "audio/sermon.mp3": "audio/mpeg",
            "audio/temoignage.m4a": "audio/mp4",
            "sermons/photo.webp": "image/webp",
            "blog/couvertures/ancienne.jpg": "image/jpeg",
        }
        for nom, attendu in cas.items():
            with self.subTest(nom=nom):
                # Type annoncé par le navigateur volontairement faux : l'extension l'emporte
                fichier = ContentFile(b"x", name=nom)
                fichier.content_type = "application/octet-stream"
                parametres = self.stockage._get_write_parameters(nom, fichier)
                self.assertEqual(parametres["ContentType"], attendu)
                self.assertEqual(parametres["CacheControl"], CACHE_CONTROL)
                self.assertNotIn("ACL", parametres)

    def test_extension_inconnue_garde_le_type_du_navigateur(self):
        fichier = ContentFile(b"x", name="divers/fichier.zzz")
        fichier.content_type = "text/plain"
        self.assertEqual(self.stockage._get_write_parameters("divers/fichier.zzz", fichier)["ContentType"], "text/plain")


class ServirMediaTests(TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dossier, True)
        (Path(self.dossier) / "audio").mkdir()
        (Path(self.dossier) / "audio" / "sermon.mp3").write_bytes(b"ID3 audio de test")

    def test_disque_sert_le_fichier(self):
        with self.settings(STORAGES=stockages_disque(self.dossier)):
            for debug in (False, True):
                with self.subTest(debug=debug), self.settings(DEBUG=debug):
                    response = self.client.get("/media/audio/sermon.mp3")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(b"".join(response.streaming_content), b"ID3 audio de test")

    def test_disque_fichier_absent(self):
        with self.settings(STORAGES=stockages_disque(self.dossier)):
            self.assertEqual(self.client.get("/media/audio/absent.mp3").status_code, 404)

    def test_r2_redirige_les_anciens_liens(self):
        config = config_stockage(ENV_R2)
        with self.settings(STORAGES=config):
            response = self.client.get("/media/audio/sermon.mp3")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://media.wmbranhamtabernacle.org/audio/sermon.mp3")

    def test_page_equipe_media_reste_prioritaire(self):
        for config in (stockages_disque(self.dossier), config_stockage(ENV_R2)):
            with self.subTest(backend=config["default"]["BACKEND"]), self.settings(STORAGES=config):
                response = self.client.get("/media/")
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "media_presse.html")


class FauxAudioSegment:
    """Remplace pydub : enregistre ce qu'il a reçu et produit un « MP3 » factice."""
    recu = []

    def __init__(self, channels=2):
        self.channels = channels

    @classmethod
    def from_file(cls, flux, format):
        cls.recu.append((flux.read(), format))
        return cls()

    def set_channels(self, n):
        return FauxAudioSegment(n)

    def export(self, sortie, format, bitrate):
        sortie.write(b"MP3 compresse mono=%d" % (self.channels == 1))


@override_settings(STORAGES=STOCKAGE_MEMOIRE)
class CompressionDesactiveeTests(TestCase):
    """Par défaut, aucun audio n'est décodé pendant la requête (risque de plantage
    de l'instance Render de 512 Mo) : le fichier envoyé est enregistré tel quel."""

    def test_audios_enregistres_tels_quels(self):
        from sermons.models import Sermons
        with mock.patch("pydub.AudioSegment.from_file", side_effect=AssertionError("pydub appelé")):
            gros_mp3 = Sermons.objects.create(titre="Long", audio=ContentFile(b"ID3" + b"x" * (6 * 1024 * 1024), name="long.mp3"))
            wav = Sermons.objects.create(titre="Wav", audio=ContentFile(b"RIFF wav", name="culte.wav"))
        self.assertEqual(gros_mp3.audio.name, "audio/long.mp3")
        self.assertEqual(gros_mp3.audio.size, 3 + 6 * 1024 * 1024)
        self.assertEqual(wav.audio.name, "audio/culte.wav")


@override_settings(STORAGES=STOCKAGE_MEMOIRE, AUDIO_COMPRESSION_ACTIVE=True)
class MixinAudioStockageDistantTests(TestCase):
    """Le mixin ne doit utiliser que l'API de stockage (open/save), jamais un chemin
    local : sur R2, FieldFile.path lève NotImplementedError. On l'interdit ici aussi
    (InMemoryStorage, lui, utilise des chemins fictifs en interne)."""

    def setUp(self):
        FauxAudioSegment.recu = []
        for patcher in (
            mock.patch("pydub.AudioSegment", FauxAudioSegment),
            mock.patch.object(FieldFile, "path", new_callable=mock.PropertyMock,
                              side_effect=NotImplementedError("pas de chemin local sur R2")),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.stockage = storages["default"]
        self.assertIsInstance(self.stockage, InMemoryStorage)

    def test_upload_compresse_et_enregistre_dans_le_stockage(self):
        from sermons.models import Sermons
        sermon = Sermons.objects.create(titre="Culte", audio=ContentFile(b"RIFF wav", name="culte.wav"))
        self.assertEqual(FauxAudioSegment.recu, [(b"RIFF wav", "wav")])
        self.assertEqual(sermon.audio.name, "audio/culte.mp3")
        with self.stockage.open(sermon.audio.name) as f:
            self.assertEqual(f.read(), b"MP3 compresse mono=1")

    def test_fichier_deja_stocke_lu_par_le_stockage(self):
        from sermons.models import Sermons
        self.stockage.save("audio/ancien.wav", ContentFile(b"RIFF ancien"))
        sermon = Sermons(titre="Ancien")
        sermon.audio.name = "audio/ancien.wav"
        with self.assertRaises(NotImplementedError):
            sermon.audio.path
        sermon.save()
        self.assertEqual(FauxAudioSegment.recu, [(b"RIFF ancien", "wav")])
        self.assertTrue(sermon.audio.name.endswith(".mp3"))

    def test_petit_mp3_enregistre_tel_quel(self):
        from sermons.models import Sermons
        sermon = Sermons.objects.create(titre="Court", audio=ContentFile(b"ID3 court", name="court.mp3"))
        self.assertEqual(FauxAudioSegment.recu, [])
        with self.stockage.open(sermon.audio.name) as f:
            self.assertEqual(f.read(), b"ID3 court")

    def test_temoignage_champ_audio_majuscule(self):
        from OurData.models import Temoignages
        temoignage = Temoignages.objects.create(Description="d", Audio=ContentFile(b"RIFF t", name="t.wav"))
        self.assertEqual(temoignage.Audio.name, "audio/t.mp3")


class MigrerMediasTests(SimpleTestCase):
    def setUp(self):
        self.disque, self.r2 = InMemoryStorage(), InMemoryStorage()
        for cible, stockage in (("stockage_disque", self.disque), ("stockage_r2", self.r2)):
            patcher = mock.patch(f"medias.management.commands.migrer_medias.{cible}", return_value=stockage)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.disque.save("audio/sermon.mp3", ContentFile(b"A" * 300))
        self.disque.save("sermons/photo.webp", ContentFile(b"B" * 50))
        self.disque.save("sermons/.DS_Store", ContentFile(b"cache"))

    def lancer(self, *args):
        sortie = StringIO()
        call_command("migrer_medias", *args, stdout=sortie, stderr=StringIO())
        return sortie.getvalue()

    def contenu(self, stockage, nom):
        with stockage.open(nom) as f:
            return f.read()

    def test_copie_puis_rejouable(self):
        self.assertIn("2 copiés", self.lancer())
        self.assertEqual(self.contenu(self.r2, "audio/sermon.mp3"), b"A" * 300)
        self.assertFalse(self.r2.exists("sermons/.DS_Store"))
        self.assertIn("0 copiés (0.0 Mo), 2 déjà présents", self.lancer())

    def test_dry_run_n_ecrit_rien(self):
        self.assertIn("2 à copier", self.lancer("--dry-run"))
        self.assertFalse(self.r2.exists("audio/sermon.mp3"))

    def test_conflit_jamais_ecrase(self):
        self.r2.save("audio/sermon.mp3", ContentFile(b"autre"))
        with self.assertRaisesMessage(CommandError, "Copie incomplète"):
            self.lancer()
        self.assertEqual(self.contenu(self.r2, "audio/sermon.mp3"), b"autre")
        self.assertTrue(self.r2.exists("sermons/photo.webp"))

    def test_verifier_detecte_un_contenu_different_de_meme_taille(self):
        self.lancer()
        self.assertIn("2/2 fichiers identiques", self.lancer("--verifier"))
        self.r2.delete("sermons/photo.webp")
        self.r2.save("sermons/photo.webp", ContentFile(b"C" * 50))
        with self.assertRaisesMessage(CommandError, "ne correspond pas"):
            self.lancer("--verifier")

    def test_retour_arriere_r2_vers_disque(self):
        self.r2.save("audio/nouveau.mp3", ContentFile(b"N" * 10))
        self.assertIn("1 copiés", self.lancer("--sens", "r2-vers-disque"))
        self.assertEqual(self.contenu(self.disque, "audio/nouveau.mp3"), b"N" * 10)


class DiagnosticR2Tests(SimpleTestCase):
    def setUp(self):
        self.r2 = InMemoryStorage()
        self.r2.custom_domain = "media.test"
        self.r2.url = lambda nom: f"https://media.test/{nom}"
        patcher = mock.patch("medias.management.commands.migrer_medias.stockage_r2", return_value=self.r2)
        patcher.start()
        self.addCleanup(patcher.stop)

    def faux_http(self, entetes):
        def lire_url(url, plage=None):
            nom = url.removeprefix("https://media.test/")
            with self.r2.open(nom) as f:
                corps = f.read()
            if plage:
                return 206, {"Content-Range": "bytes 100-199/4096"}, corps[100:200]
            return 200, entetes, corps
        return mock.patch("medias.management.commands.migrer_medias.lire_url", side_effect=lire_url)

    def test_diagnostic_reussi_et_nettoye(self):
        with self.faux_http({"Content-Type": "audio/mpeg", "Cache-Control": CACHE_CONTROL}):
            sortie = StringIO()
            call_command("migrer_medias", "--diagnostic", stdout=sortie)
        self.assertIn("R2 est prêt pour la bascule", sortie.getvalue())
        self.assertEqual(self.r2.listdir("_diagnostic")[1], [])

    def test_diagnostic_en_echec_sans_cache_control(self):
        with self.faux_http({"Content-Type": "audio/mpeg"}):
            with self.assertRaisesMessage(CommandError, "ne pas basculer"):
                call_command("migrer_medias", "--diagnostic", stdout=StringIO())
        self.assertEqual(self.r2.listdir("_diagnostic")[1], [])
