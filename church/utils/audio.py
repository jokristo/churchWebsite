"""Compression des audios envoyés depuis l'admin (sermons, témoignages).

- FFmpeg lit et écrit des fichiers sur disque : la mémoire reste constante (environ
  20 Mo) quelle que soit la durée. L'ancienne méthode (pydub) décodait tout l'audio
  en mémoire, environ 32 Mo par minute : un sermon long faisait planter l'instance.
- La compression a lieu après la requête, dans un fil d'exécution en arrière-plan,
  pour ne dépasser ni le délai de gunicorn (30 s) ni bloquer le site. La commande
  compresser_audios rattrape ce qui a été interrompu (redéploiement, redémarrage).
- Parole : MP3 mono à AUDIO_DEBIT (64 kbps par défaut), standard des podcasts.
- L'original reste dans le stockage ; son nom est gardé dans audio_original.
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
import threading

from django.conf import settings
from django.core.files import File
from django.db import connection, models, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

EN_ATTENTE, EN_COURS, COMPRESSE, IGNORE, ECHEC = "en_attente", "en_cours", "compresse", "ignore", "echec"
ETATS = [
    ("", "Non traité"),
    (EN_ATTENTE, "En attente"),
    (EN_COURS, "En cours"),
    (COMPRESSE, "Compressé"),
    (IGNORE, "Laissé tel quel"),
    (ECHEC, "Échec"),
]
DELAI_MAX_SECONDES = 30 * 60
BLOC = 1024 * 1024


class ErreurAudio(Exception):
    pass


def compression_active():
    return getattr(settings, "AUDIO_COMPRESSION_ACTIVE", False)


def debit_cible():
    return getattr(settings, "AUDIO_DEBIT", "64k")


def _bps(debit):
    return int(debit.lower().rstrip("k")) * 1000


def _mo(octets):
    return f"{octets / 1048576:.1f} Mo"


def audio_field_changed(instance, field_name="audio"):
    field = getattr(instance, field_name, None)
    if not field:
        return False
    if not instance.pk:
        return True
    old_name = (
        instance.__class__.objects.filter(pk=instance.pk)
        .values_list(field_name, flat=True)
        .first()
    )
    return field.name != old_name


def analyser(chemin):
    """Codec, nombre de canaux et débit (bit/s, ou None) du premier flux audio."""
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_name,channels,bit_rate:format=bit_rate",
         "-of", "json", chemin],
        capture_output=True, text=True, timeout=120,
    )
    try:
        donnees = json.loads(resultat.stdout or "{}")
        flux = donnees["streams"][0]
    except (ValueError, KeyError, IndexError):
        raise ErreurAudio("fichier audio illisible") from None
    debit = flux.get("bit_rate") or donnees.get("format", {}).get("bit_rate")
    return {
        "codec": flux.get("codec_name"),
        "canaux": int(flux.get("channels") or 0),
        "debit": int(debit) if debit and str(debit).isdigit() else None,
    }


def deja_leger(info, debit):
    return (
        info["codec"] == "mp3"
        and info["canaux"] == 1
        and info["debit"] is not None
        and info["debit"] <= _bps(debit) * 1.1
    )


def encoder(entree, sortie, debit):
    commande = [
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-threads", "1",
        "-i", entree, "-vn", "-ac", "1", "-codec:a", "libmp3lame", "-b:a", debit,
        "-map_metadata", "0", "-id3v2_version", "3", sortie,
    ]
    # Priorité basse : le site reste prioritaire sur le processeur pendant l'encodage.
    if shutil.which("nice"):
        commande = ["nice", "-n", "19"] + commande
    delai = getattr(settings, "AUDIO_COMPRESSION_DELAI", DELAI_MAX_SECONDES)
    try:
        resultat = subprocess.run(commande, capture_output=True, text=True, timeout=delai)
    except subprocess.TimeoutExpired:
        raise ErreurAudio(f"encodage interrompu après {delai // 60} min") from None
    if resultat.returncode != 0:
        raise ErreurAudio(f"FFmpeg a échoué : {resultat.stderr.strip()[-200:]}")


def _terminer(modele, pk, nom_source, etat, detail):
    modele.objects.filter(pk=pk, **{modele.audio_field_name: nom_source}).update(
        audio_etat=etat, audio_detail=detail[:255], audio_maj=timezone.now()
    )
    return etat


def compresser(modele, pk):
    """Compresse l'audio d'un objet en attente. Renvoie l'état final, ou None si l'objet
    n'était pas en attente (déjà pris en charge par un autre traitement)."""
    champ = modele.audio_field_name
    pris = modele.objects.filter(pk=pk, audio_etat=EN_ATTENTE).update(
        audio_etat=EN_COURS, audio_maj=timezone.now()
    )
    if not pris:
        return None

    instance = modele.objects.get(pk=pk)
    fichier = getattr(instance, champ)
    nom_source = fichier.name
    debit = debit_cible()
    with tempfile.TemporaryDirectory(prefix="compression-audio-") as dossier:
        try:
            # Copie en flux vers le disque local (le stockage peut être R2) : jamais
            # tout le fichier en mémoire.
            entree = os.path.join(dossier, "source" + os.path.splitext(nom_source)[1].lower())
            with fichier.storage.open(nom_source, "rb") as source, open(entree, "wb") as copie:
                shutil.copyfileobj(source, copie, BLOC)

            info = analyser(entree)
            if deja_leger(info, debit):
                return _terminer(modele, pk, nom_source, IGNORE,
                                 f"déjà léger : {info['debit'] // 1000} kbps mono")

            sortie = os.path.join(dossier, "compresse.mp3")
            encoder(entree, sortie, debit)
            avant, apres = os.path.getsize(entree), os.path.getsize(sortie)
            if apres == 0:
                raise ErreurAudio("FFmpeg a produit un fichier vide")
            if apres >= avant * 0.95:
                return _terminer(modele, pk, nom_source, IGNORE,
                                 f"aucun gain : {_mo(avant)} → {_mo(apres)}")

            base = os.path.splitext(os.path.basename(nom_source))[0]
            champ_fichier = getattr(modele, champ).field
            nom_cible = champ_fichier.generate_filename(instance, f"{base}-{debit}.mp3")
            with open(sortie, "rb") as flux:
                # max_length : le stockage raccourcit le nom si besoin (colonne de 100 caractères)
                nom_ecrit = fichier.storage.save(nom_cible, File(flux, name=nom_cible),
                                                 max_length=champ_fichier.max_length)

            # Si l'audio a été remplacé dans l'admin pendant l'encodage, on ne touche à rien.
            remplace = modele.objects.filter(pk=pk, **{champ: nom_source}).update(**{
                champ: nom_ecrit,
                "audio_original": nom_source,
                "audio_etat": COMPRESSE,
                "audio_detail": f"{_mo(avant)} → {_mo(apres)} ({debit} mono)",
                "audio_maj": timezone.now(),
            })
            if not remplace:
                fichier.storage.delete(nom_ecrit)
                return None
            logger.info("Audio compressé %s : %s -> %s", nom_source, _mo(avant), _mo(apres))
            return COMPRESSE
        except Exception as exc:
            logger.exception("Compression de %s impossible", nom_source)
            return _terminer(modele, pk, nom_source, ECHEC, str(exc) or exc.__class__.__name__)


def lancer(modele, pk):
    """Compression en arrière-plan (ou immédiate si AUDIO_COMPRESSION_SYNCHRONE, en test)."""
    if getattr(settings, "AUDIO_COMPRESSION_SYNCHRONE", False):
        compresser(modele, pk)
        return

    def tache():
        try:
            compresser(modele, pk)
        finally:
            connection.close()  # connexion à la base propre à ce fil d'exécution

    threading.Thread(target=tache, name=f"compression-audio-{modele.__name__}-{pk}", daemon=True).start()


def demander_compression(instance):
    """Marque l'objet en attente et lance la compression après validation en base."""
    modele, pk = type(instance), instance.pk
    modele.objects.filter(pk=pk).update(audio_etat=EN_ATTENTE, audio_detail="", audio_maj=timezone.now())
    transaction.on_commit(lambda: lancer(modele, pk))


class AudioCompressionMixin(models.Model):
    """À hériter par les modèles qui ont un champ audio (nom dans audio_field_name)."""

    audio_field_name = "audio"

    audio_etat = models.CharField("Compression audio", max_length=12, choices=ETATS,
                                  blank=True, default="", editable=False)
    audio_original = models.CharField("Fichier audio original", max_length=255,
                                      blank=True, default="", editable=False)
    audio_detail = models.CharField("Détail de la compression", max_length=255,
                                    blank=True, default="", editable=False)
    audio_maj = models.DateTimeField("Compression mise à jour le", null=True, blank=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        change = audio_field_changed(self, self.audio_field_name)
        nouveau = change and compression_active()
        if nouveau:
            self.audio_etat, self.audio_original, self.audio_detail = EN_ATTENTE, "", ""
            self.audio_maj = timezone.now()
        elif change or not getattr(self, self.audio_field_name):
            # Nouvel audio sans compression, ou audio retiré : l'ancien état ne vaut plus.
            self.audio_etat, self.audio_original, self.audio_detail = "", "", ""
        super().save(*args, **kwargs)
        if nouveau:
            modele, pk = type(self), self.pk
            transaction.on_commit(lambda: lancer(modele, pk))
