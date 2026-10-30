"""Synchronisation incrémentale de l'application mobile.

1. Toute disparition d'un contenu de l'API (suppression, dépublication d'un article,
   désapprobation d'un témoignage) laisse une trace dans Suppression.
2. Les sermons et les articles intègrent le nom de leur orateur, thème ou catégorie :
   quand ce nom change ou disparaît, leur date_modification est mise à jour pour que
   l'application les retélécharge.
"""
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from actualites.models import Article, Categorie
from api.models import Suppression
from OurData.models import Ministre, Temoignages
from sermons.models import Orateur, Sermons, Theme

TYPES = {
    Sermons: "sermon",
    Theme: "theme",
    Orateur: "orateur",
    Ministre: "ministre",
    Article: "article",
    Temoignages: "temoignage",
}


def _tracer(modele, pk, motif):
    Suppression.objects.create(type=TYPES[modele], objet_id=pk, motif=motif)


@receiver(post_delete)
def trace_suppression(sender, instance, **kwargs):
    if sender in TYPES:
        _tracer(sender, instance.pk, Suppression.SUPPRIME)


# --- Retrait de l'API sans suppression : article dépublié, témoignage désapprouvé ---

VISIBILITE = {Article: ("est_publie", Suppression.DEPUBLIE), Temoignages: ("is_Approuve", Suppression.DESAPPROUVE)}


@receiver(pre_save)
def memorise_visibilite(sender, instance, **kwargs):
    if sender in VISIBILITE and instance.pk:
        champ, _ = VISIBILITE[sender]
        instance._etait_visible = sender.objects.filter(pk=instance.pk).values_list(champ, flat=True).first()


@receiver(post_save)
def trace_retrait(sender, instance, created, **kwargs):
    if sender in VISIBILITE and not created:
        champ, motif = VISIBILITE[sender]
        if getattr(instance, "_etait_visible", False) and not getattr(instance, champ):
            _tracer(sender, instance.pk, motif)


# --- Noms intégrés : redater les contenus qui les affichent ---

def _redater(queryset):
    queryset.update(date_modification=timezone.now())


@receiver(post_save, sender=Orateur)
@receiver(pre_delete, sender=Orateur)
def redate_sermons_orateur(sender, instance, **kwargs):
    _redater(Sermons.objects.filter(orateur=instance))


@receiver(post_save, sender=Theme)
@receiver(pre_delete, sender=Theme)
def redate_sermons_theme(sender, instance, **kwargs):
    _redater(Sermons.objects.filter(Theme=instance))


@receiver(pre_delete, sender=Ministre)
def redate_liens_ministre(sender, instance, **kwargs):
    # Orateurs et thèmes exposent ministre_id, qui passera à null
    _redater(Orateur.objects.filter(ministre=instance))
    _redater(Theme.objects.filter(ministre=instance))


@receiver(post_save, sender=Categorie)
@receiver(pre_delete, sender=Categorie)
def redate_articles_categorie(sender, instance, **kwargs):
    _redater(Article.objects.filter(categorie=instance))
