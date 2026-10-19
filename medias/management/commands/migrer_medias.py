"""Copie les médias entre le disque (MEDIA_ROOT) et Cloudflare R2.

Utilisable avant la bascule (MEDIA_STORAGE n'a pas besoin d'être défini) :

    python manage.py migrer_medias --diagnostic      # teste R2 de bout en bout
    python manage.py migrer_medias --dry-run         # liste ce qui serait copié
    python manage.py migrer_medias                   # copie disque -> R2
    python manage.py migrer_medias --verifier        # compare taille + MD5
    python manage.py migrer_medias --sens r2-vers-disque   # retour arrière

Rejouable : un fichier déjà présent avec la même taille est ignoré. Rien n'est jamais
écrasé : un fichier présent des deux côtés avec une taille différente est signalé
comme conflit et laissé tel quel.
"""
import hashlib
import io
import os
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError

from church.stockage import CACHE_CONTROL, options_r2

DOSSIER_DIAGNOSTIC = "_diagnostic"


def stockage_disque():
    return FileSystemStorage(location=settings.MEDIA_ROOT)


def stockage_r2():
    from medias.stockage import StockageR2
    try:
        return StockageR2(**options_r2(os.environ))
    except ImproperlyConfigured as exc:
        raise CommandError(f"{exc} (variables à définir dans Render > Environment)") from exc


def lister(stockage, dossier=""):
    """Tous les fichiers d'un stockage, récursivement, sans les fichiers cachés."""
    dossiers, fichiers = stockage.listdir(dossier)
    for nom in fichiers:
        if not nom.startswith("."):
            yield f"{dossier}/{nom}" if dossier else nom
    for sous in dossiers:
        if sous.startswith(".") or (not dossier and sous == DOSSIER_DIAGNOSTIC):
            continue
        yield from lister(stockage, f"{dossier}/{sous}" if dossier else sous)


def empreinte(stockage, nom):
    md5 = hashlib.md5()
    with stockage.open(nom, "rb") as fichier:
        for bloc in iter(lambda: fichier.read(1024 * 1024), b""):
            md5.update(bloc)
    return md5.hexdigest()


def lire_url(url, plage=None):
    """GET HTTP (statut, en-têtes, corps), sans lever d'exception sur 4xx/5xx."""
    requete = urllib.request.Request(url, headers={"User-Agent": "WMB-diagnostic-medias"})
    if plage:
        requete.add_header("Range", plage)
    try:
        with urllib.request.urlopen(requete, timeout=20) as reponse:
            return reponse.status, reponse.headers, reponse.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, b""


def taille_lisible(octets):
    return f"{octets / 1048576:.1f} Mo"


class Command(BaseCommand):
    help = "Copie et vérifie les médias entre le disque et Cloudflare R2."

    def add_arguments(self, parser):
        parser.add_argument("--sens", choices=["disque-vers-r2", "r2-vers-disque"], default="disque-vers-r2")
        parser.add_argument("--dry-run", action="store_true", help="N'écrit rien, liste ce qui serait copié.")
        parser.add_argument("--verifier", action="store_true", help="Compare taille et MD5 de chaque fichier, sans copier.")
        parser.add_argument("--diagnostic", action="store_true", help="Teste l'écriture, l'URL publique, les en-têtes et Range sur R2.")

    def handle(self, *args, sens, dry_run, verifier, diagnostic, **options):
        if diagnostic:
            return self.diagnostic()
        disque, r2 = stockage_disque(), stockage_r2()
        source, destination = (disque, r2) if sens == "disque-vers-r2" else (r2, disque)
        self.stdout.write(f"Sens : {sens} | disque : {disque.location} | bucket : {getattr(r2, 'bucket_name', '?')}")
        if verifier:
            return self.verifier(source, destination)
        self.copier(source, destination, dry_run)

    def copier(self, source, destination, dry_run):
        copies, deja, conflits, erreurs, octets = [], 0, [], [], 0
        for nom in sorted(lister(source)):
            taille = source.size(nom)
            if destination.exists(nom):
                if destination.size(nom) == taille:
                    deja += 1
                else:
                    conflits.append(nom)
                    self.stderr.write(f"CONFLIT (tailles différentes, rien n'est écrasé) : {nom}")
                continue
            if dry_run:
                self.stdout.write(f"à copier : {nom} ({taille_lisible(taille)})")
                copies.append(nom)
                octets += taille
                continue
            try:
                with source.open(nom, "rb") as fichier:
                    ecrit = destination.save(nom, File(fichier, name=nom))
                if ecrit != nom:
                    raise CommandError(f"enregistré sous un autre nom : {ecrit}")
                if destination.size(nom) != taille:
                    raise CommandError("taille différente après copie")
            except Exception as exc:  # on continue avec les autres fichiers, bilan à la fin
                erreurs.append(nom)
                self.stderr.write(f"ERREUR {nom} : {exc}")
                continue
            copies.append(nom)
            octets += taille
            self.stdout.write(f"copié : {nom} ({taille_lisible(taille)})")

        verbe = "à copier" if dry_run else "copiés"
        self.stdout.write(
            f"\nBilan : {len(copies)} {verbe} ({taille_lisible(octets)}), {deja} déjà présents, "
            f"{len(conflits)} conflit(s), {len(erreurs)} erreur(s)."
        )
        if conflits or erreurs:
            raise CommandError("Copie incomplète : voir les conflits et erreurs ci-dessus.")

    def verifier(self, source, destination):
        absents, differents, ok, octets = [], [], 0, 0
        noms = sorted(lister(source))
        for nom in noms:
            if not destination.exists(nom):
                absents.append(nom)
                continue
            taille = source.size(nom)
            if destination.size(nom) != taille or empreinte(source, nom) != empreinte(destination, nom):
                differents.append(nom)
                continue
            ok += 1
            octets += taille
        for nom in absents:
            self.stderr.write(f"ABSENT : {nom}")
        for nom in differents:
            self.stderr.write(f"DIFFÉRENT : {nom}")
        en_plus = len(set(lister(destination)) - set(noms))
        self.stdout.write(
            f"\nVérification : {ok}/{len(noms)} fichiers identiques ({taille_lisible(octets)}), "
            f"{len(absents)} absent(s), {len(differents)} différent(s), "
            f"{en_plus} fichier(s) présents uniquement à destination."
        )
        if absents or differents:
            raise CommandError("La destination ne correspond pas à la source.")

    def diagnostic(self):
        r2 = stockage_r2()
        nom = f"{DOSSIER_DIAGNOSTIC}/test-{int(time.time())}.mp3"
        contenu = os.urandom(4096)
        resultats = []

        def controle(libelle, condition, detail=""):
            resultats.append(condition)
            marque = self.style.SUCCESS("OK  ") if condition else self.style.ERROR("ÉCHEC")
            self.stdout.write(f"{marque} {libelle}{' — ' + detail if detail else ''}")

        self.stdout.write(f"Bucket : {getattr(r2, 'bucket_name', '?')} | domaine public : {r2.custom_domain}")
        try:
            ecrit = r2.save(nom, File(io.BytesIO(contenu), name=nom))
            controle("écriture dans le bucket (jeton et endpoint valides)", ecrit == nom, ecrit)
            url = r2.url(nom)
            controle("URL publique sans signature", "?" not in url and url.startswith(f"https://{r2.custom_domain}/"), url)

            statut, entetes, corps = lire_url(url)
            controle("lecture par le domaine public", statut == 200 and corps == contenu, f"HTTP {statut}")
            controle("Content-Type", entetes.get("Content-Type") == "audio/mpeg", entetes.get("Content-Type", "absent"))
            controle("Cache-Control", entetes.get("Cache-Control") == CACHE_CONTROL, entetes.get("Cache-Control", "absent"))

            statut, entetes, corps = lire_url(url, "bytes=100-199")
            controle(
                "lecture partielle (Range) pour avancer dans un audio",
                statut == 206 and corps == contenu[100:200],
                f"HTTP {statut}, {entetes.get('Content-Range', 'pas de Content-Range')}",
            )
        finally:
            try:
                r2.delete(nom)
                self.stdout.write("Fichier de test supprimé.")
            except Exception as exc:
                self.stderr.write(f"Impossible de supprimer {nom} : {exc}")

        if not all(resultats):
            raise CommandError("Diagnostic en échec : ne pas basculer avant d'avoir corrigé.")
        self.stdout.write(self.style.SUCCESS("\nR2 est prêt pour la bascule."))
