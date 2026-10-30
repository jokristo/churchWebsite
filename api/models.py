from django.db import models


class Suppression(models.Model):
    """Trace d'un contenu qui a disparu de l'API, pour la synchronisation incrémentale :
    sans elle, l'application garderait hors ligne un sermon supprimé ou un article dépublié.
    Remplie automatiquement par api/signals.py, jamais à la main."""

    SUPPRIME, DEPUBLIE, DESAPPROUVE = "supprime", "depublie", "desapprouve"
    MOTIFS = [(SUPPRIME, "Supprimé"), (DEPUBLIE, "Dépublié"), (DESAPPROUVE, "Désapprouvé")]

    type = models.CharField(max_length=20, db_index=True)
    objet_id = models.PositiveBigIntegerField()
    motif = models.CharField(max_length=12, choices=MOTIFS)
    date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Suppression (synchronisation)"
        verbose_name_plural = "Suppressions (synchronisation)"
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.type} #{self.objet_id} {self.get_motif_display().lower()} le {self.date:%d/%m/%Y}"
