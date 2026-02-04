from django.db import models

class EvolutionConstruction(models.Model):
    titre = models.CharField(max_length=100)
    image = models.ImageField(upload_to='construction/evolution/')
    date_travaux = models.DateField("Date des travaux")
    description = models.TextField(blank=True)
    date_publication = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_travaux'] # Les plus récents en premier

    def __str__(self):
        return f"{self.titre} - {self.date_travaux}"

class Contribution(models.Model):
    nom_donateur = models.CharField("Nom (Laisser vide pour Anonyme)", max_length=100, blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2) # Ex: 100.00 $
    transaction_id = models.CharField("ID Transaction PayPal", max_length=100, unique=True)
    date_don = models.DateTimeField(auto_now_add=True)
    
    # Optionnel: Message d'encouragement
    message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_don']

    def __str__(self):
        nom = self.nom_donateur if self.nom_donateur else "Anonyme"
        return f"{self.montant}$ par {nom}"