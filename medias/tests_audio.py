"""Compression audio en flux (church/utils/audio.py), testée avec le vrai FFmpeg."""
import os
import shutil
import subprocess
import tempfile
import tracemalloc
from datetime import timedelta
from io import StringIO
from unittest import mock, skipUnless

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from church.stockage import STATICFILES
from church.utils import audio
from church.utils.audio import COMPRESSE, ECHEC, EN_ATTENTE, EN_COURS, IGNORE

FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def generer_mp3(chemin, secondes, canaux=2, debit="128k"):
    """Faux sermon : sinusoïde + bruit rose, pour que l'encodeur ait du contenu à compresser."""
    disposition = "mono" if canaux == 1 else "stereo"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=44100:duration={secondes}",
         "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.05:sample_rate=44100:duration={secondes}",
         "-filter_complex", f"[0][1]amix=inputs=2,aformat=channel_layouts={disposition}",
         "-c:a", "libmp3lame", "-b:a", debit, chemin],
        check=True,
    )


@skipUnless(FFMPEG, "FFmpeg et ffprobe requis")
class CompressionAudioTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sources = tempfile.mkdtemp()
        cls.stereo = os.path.join(cls.sources, "stereo.mp3")
        cls.mono_leger = os.path.join(cls.sources, "mono.mp3")
        generer_mp3(cls.stereo, 30)
        generer_mp3(cls.mono_leger, 30, canaux=1, debit="64k")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.sources, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.medias = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.medias, True)
        disque = {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": self.medias}}
        self.enterContext(self.settings(
            STORAGES={"default": disque, "staticfiles": STATICFILES},
            AUDIO_COMPRESSION_ACTIVE=True, AUDIO_COMPRESSION_SYNCHRONE=True, AUDIO_DEBIT="64k",
        ))
        self.stockage = storages["default"]

    def envoyer(self, chemin, nom, modele=None, champ="audio", **champs):
        from sermons.models import Sermons
        modele = modele or Sermons
        champs.setdefault("titre", "Culte") if modele is Sermons else champs.setdefault("Description", "d")
        with open(chemin, "rb") as f, self.captureOnCommitCallbacks(execute=True):
            objet = modele.objects.create(**{champ: File(f, name=nom)}, **champs)
        objet.refresh_from_db()
        return objet

    def sonder(self, nom):
        with tempfile.NamedTemporaryFile(suffix=".mp3") as copie:
            with self.stockage.open(nom, "rb") as source:
                shutil.copyfileobj(source, copie)
            copie.flush()
            return audio.analyser(copie.name)

    def test_stereo_compresse_en_mono_64k_et_original_conserve(self):
        sermon = self.envoyer(self.stereo, "sermon.mp3")
        self.assertEqual(sermon.audio_etat, COMPRESSE)
        self.assertEqual(sermon.audio.name, "audio/sermon-64k.mp3")
        self.assertEqual(sermon.audio_original, "audio/sermon.mp3")
        self.assertTrue(self.stockage.exists("audio/sermon.mp3"))
        info = self.sonder(sermon.audio.name)
        self.assertEqual(info["canaux"], 1)
        self.assertAlmostEqual(info["debit"], 64000, delta=6400)
        self.assertLess(self.stockage.size(sermon.audio.name), self.stockage.size("audio/sermon.mp3") * 0.6)
        self.assertIn("→", sermon.audio_detail)
        # Mesures exposées par l'API : celles du fichier compressé
        self.assertEqual(sermon.audio_taille, self.stockage.size(sermon.audio.name))
        self.assertAlmostEqual(sermon.audio_duree, 30, delta=1)

    def test_fichier_deja_leger_laisse_tel_quel(self):
        sermon = self.envoyer(self.mono_leger, "court.mp3")
        self.assertEqual(sermon.audio_etat, IGNORE)
        self.assertEqual(sermon.audio.name, "audio/court.mp3")
        self.assertEqual(sermon.audio_original, "")
        self.assertIn("déjà léger", sermon.audio_detail)

    def test_fichier_illisible_reste_disponible_et_signale(self):
        from sermons.models import Sermons
        with self.captureOnCommitCallbacks(execute=True):
            sermon = Sermons.objects.create(titre="Faux", audio=ContentFile(b"pas un audio", name="faux.mp3"))
        sermon.refresh_from_db()
        self.assertEqual(sermon.audio_etat, ECHEC)
        self.assertEqual(sermon.audio.name, "audio/faux.mp3")
        self.assertIn("illisible", sermon.audio_detail)

    def test_temoignage_champ_audio_majuscule(self):
        from OurData.models import Temoignages
        temoignage = self.envoyer(self.stereo, "temoignage.mp3", modele=Temoignages, champ="Audio")
        self.assertEqual(temoignage.audio_etat, COMPRESSE)
        self.assertEqual(temoignage.Audio.name, "audio/temoignage-64k.mp3")

    def test_compression_desactivee_mesure_quand_meme(self):
        # L'API a besoin de la taille et de la durée, même sans compression
        with self.settings(AUDIO_COMPRESSION_ACTIVE=False):
            sermon = self.envoyer(self.stereo, "brut.mp3")
        self.assertEqual(sermon.audio_etat, IGNORE)
        self.assertEqual(sermon.audio_detail, "compression désactivée")
        self.assertEqual(sermon.audio.name, "audio/brut.mp3")
        self.assertEqual(sermon.audio_taille, self.stockage.size("audio/brut.mp3"))
        self.assertAlmostEqual(sermon.audio_duree, 30, delta=1)

    def test_commande_mesurer_sans_recompresser(self):
        from sermons.models import Sermons
        sermon = self.envoyer(self.stereo, "deja.mp3")
        Sermons.objects.filter(pk=sermon.pk).update(audio_taille=None, audio_duree=None)
        sortie = StringIO()
        call_command("compresser_audios", "--mesurer", stdout=sortie)
        sermon.refresh_from_db()
        self.assertEqual(sermon.audio.name, "audio/deja-64k.mp3")  # pas recompressé
        self.assertEqual(sermon.audio_taille, self.stockage.size(sermon.audio.name))
        self.assertAlmostEqual(sermon.audio_duree, 30, delta=1)
        self.assertIn("1 audio(s) traité(s)", sortie.getvalue())

    def test_jamais_traite_deux_fois(self):
        from sermons.models import Sermons
        sermon = self.envoyer(self.stereo, "sermon.mp3")
        self.assertIsNone(audio.compresser(Sermons, sermon.pk))

    def test_audio_remplace_pendant_l_encodage(self):
        from sermons.models import Sermons
        with self.settings(AUDIO_COMPRESSION_ACTIVE=False):
            sermon = self.envoyer(self.stereo, "ancien.mp3")
        Sermons.objects.filter(pk=sermon.pk).update(audio_etat=EN_ATTENTE)
        encoder = audio.encoder

        def encoder_puis_remplacer(*args):
            encoder(*args)
            Sermons.objects.filter(pk=sermon.pk).update(audio="audio/nouveau.mp3")

        with mock.patch.object(audio, "encoder", side_effect=encoder_puis_remplacer):
            self.assertIsNone(audio.compresser(Sermons, sermon.pk))
        sermon.refresh_from_db()
        self.assertEqual(sermon.audio.name, "audio/nouveau.mp3")
        self.assertFalse(self.stockage.exists("audio/ancien-64k.mp3"))

    def test_nom_long_tient_dans_la_colonne(self):
        sermon = self.envoyer(self.stereo, "p" * 90 + ".mp3")
        self.assertEqual(sermon.audio_etat, COMPRESSE)
        self.assertLessEqual(len(sermon.audio.name), 100)

    def test_delai_depasse(self):
        with self.settings(AUDIO_COMPRESSION_DELAI=0.001):
            sermon = self.envoyer(self.stereo, "lent.mp3")
        self.assertEqual(sermon.audio_etat, ECHEC)
        self.assertIn("interrompu", sermon.audio_detail)
        self.assertEqual(sermon.audio.name, "audio/lent.mp3")

    def test_memoire_constante(self):
        # 6 min stéréo 256 kbps (11 Mo) : l'ancienne méthode aurait alloué environ 190 Mo.
        from sermons.models import Sermons
        long = os.path.join(self.medias, "long_source.mp3")
        generer_mp3(long, 360, debit="256k")
        with self.settings(AUDIO_COMPRESSION_ACTIVE=False):
            sermon = self.envoyer(long, "long.mp3")
        Sermons.objects.filter(pk=sermon.pk).update(audio_etat=EN_ATTENTE)
        tracemalloc.start()
        try:
            self.assertEqual(audio.compresser(Sermons, sermon.pk), COMPRESSE)
            _, pic = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(pic, 4 * 1024 * 1024, f"pic mémoire Python : {pic / 1048576:.1f} Mo")

    def test_action_admin_recompresser(self):
        from django.contrib.auth import get_user_model
        with self.settings(AUDIO_COMPRESSION_ACTIVE=False):
            sermon = self.envoyer(self.stereo, "admin.mp3")
        admin = get_user_model().objects.create_superuser("admin", "a@a.org", "motdepasse")
        self.client.force_login(admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("admin:sermons_sermons_changelist"), {
                "action": "recompresser_audio", "_selected_action": [sermon.pk],
            })
        self.assertEqual(response.status_code, 302)
        sermon.refresh_from_db()
        self.assertEqual(sermon.audio_etat, COMPRESSE)
        page = self.client.get(reverse("admin:sermons_sermons_change", args=[sermon.pk]))
        self.assertContains(page, "Compressé")

    def test_commande_existants_et_interrompus(self):
        from sermons.models import Sermons
        with self.settings(AUDIO_COMPRESSION_ACTIVE=False):
            ancien = self.envoyer(self.stereo, "ancien.mp3")
            interrompu = self.envoyer(self.stereo, "interrompu.mp3")
        # « ancien » : envoyé avant l'arrivée de la compression (jamais traité)
        Sermons.objects.filter(pk=ancien.pk).update(audio_etat="")
        Sermons.objects.filter(pk=interrompu.pk).update(audio_etat=EN_COURS, audio_maj=timezone.now() - timedelta(hours=2))

        sortie = StringIO()
        call_command("compresser_audios", "--dry-run", "--existants", stdout=sortie)
        self.assertIn("2 audio(s) à traiter", sortie.getvalue())

        call_command("compresser_audios", stdout=StringIO())
        self.assertEqual(Sermons.objects.get(pk=interrompu.pk).audio_etat, COMPRESSE)
        self.assertEqual(Sermons.objects.get(pk=ancien.pk).audio_etat, "")

        sortie = StringIO()
        call_command("compresser_audios", "--existants", stdout=sortie)
        self.assertEqual(Sermons.objects.get(pk=ancien.pk).audio_etat, COMPRESSE)
        self.assertIn("1 compressé(s)", sortie.getvalue())
