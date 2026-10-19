"""Compresse les audios des sermons et témoignages (voir church/utils/audio.py).

    python manage.py compresser_audios --dry-run     # liste ce qui serait traité
    python manage.py compresser_audios               # en attente + traitements interrompus
    python manage.py compresser_audios --existants   # + audios jamais traités (envoyés avant)
    python manage.py compresser_audios --echecs      # + nouvel essai des échecs

Le traitement se fait ici, sans fil d'exécution : la commande attend la fin de chaque
compression. Les originaux sont conservés dans le stockage.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from church.utils.audio import COMPRESSE, ECHEC, EN_ATTENTE, EN_COURS, IGNORE, compresser

# Un traitement « en cours » depuis plus longtemps a été interrompu (redéploiement…).
DELAI_INTERROMPU = timedelta(hours=1)


def modeles_audio():
    from OurData.models import Temoignages
    from sermons.models import Sermons
    return [Sermons, Temoignages]


class Command(BaseCommand):
    help = "Compresse les audios en attente, interrompus, existants ou en échec."

    def add_arguments(self, parser):
        parser.add_argument("--existants", action="store_true", help="Inclut les audios jamais traités.")
        parser.add_argument("--echecs", action="store_true", help="Réessaie les audios en échec.")
        parser.add_argument("--dry-run", action="store_true", help="N'encode rien, liste seulement.")

    def handle(self, *args, existants, echecs, dry_run, **options):
        etats = Q(audio_etat=EN_ATTENTE) | Q(audio_etat=EN_COURS, audio_maj__lt=timezone.now() - DELAI_INTERROMPU)
        if existants:
            etats |= Q(audio_etat="")
        if echecs:
            etats |= Q(audio_etat=ECHEC)

        bilan = {COMPRESSE: 0, IGNORE: 0, ECHEC: 0, None: 0}
        for modele in modeles_audio():
            champ = modele.audio_field_name
            for objet in modele.objects.filter(etats).exclude(**{champ: ""}).exclude(**{f"{champ}__isnull": True}).order_by("pk"):
                nom = getattr(objet, champ).name
                if dry_run:
                    self.stdout.write(f"à traiter : {modele.__name__} #{objet.pk} {nom} ({objet.get_audio_etat_display()})")
                    bilan[None] += 1
                    continue
                modele.objects.filter(pk=objet.pk).update(audio_etat=EN_ATTENTE)
                etat = compresser(modele, objet.pk)
                bilan[etat] += 1
                detail = modele.objects.values_list("audio_detail", flat=True).get(pk=objet.pk)
                self.stdout.write(f"{etat or 'déjà pris en charge'} : {modele.__name__} #{objet.pk} {nom} — {detail}")

        if dry_run:
            self.stdout.write(f"\nBilan : {bilan[None]} audio(s) à traiter.")
        else:
            self.stdout.write(
                f"\nBilan : {bilan[COMPRESSE]} compressé(s), {bilan[IGNORE]} laissé(s) tel(s) quel(s), "
                f"{bilan[ECHEC]} échec(s)."
            )
