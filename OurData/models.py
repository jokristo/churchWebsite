from django.db import models


# Create your models here.
class Ministre(models.Model):
    Nom = models.CharField(max_length=100, blank=False)
    photo = models.ImageField(blank=True, upload_to='ministrespictures')
    contact = models.CharField(max_length=25, blank=True)

    class Meta:
        verbose_name = 'Ministre'

    def __str__(self):
        return self.Nom



class CategorieOfficiel(models.Model):
    Nom = models.CharField(max_length=100, blank= False)

    def __str__(self):
        return self.Nom


class Officiel(models.Model):
    Nom = models.CharField(max_length=100, blank=False)
    fonction = models.CharField(max_length=50, blank=False)
    contact = models.CharField(max_length=20, blank=False)
    photo = models.ImageField(blank=True, upload_to='officielpictures')
    categorieOfficiel = models.ForeignKey(CategorieOfficiel, on_delete=models.SET_NULL, null=True )

    class Meta:
        verbose_name = 'Officiel'

    def __str__(self):
        return self.Nom


class Temoignages(models.Model):
    NomDuCroyant = models.CharField(max_length=100, blank=True)
    Audio = models.FileField(blank=True, upload_to='audio', null=True)
    Description = models.TextField(blank=False)
    photo = models.ImageField(blank=True, upload_to='temoignagespictures', null=True)
    is_Approuve = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Temoignage'

    def __str__(self):
        return self.NomDuCroyant


class Evenements(models.Model):
    NomEvenement = models.CharField(max_length=200, blank=False)
    Date = models.DateField(blank=False)
    VideoEvenement = models.FileField(blank=True, upload_to='VideoEvenement')
    VisuelEvenement = models.ImageField(blank=True, upload_to='EvenementVisuel')

    class Meta:
        verbose_name = 'Evenement'

    def __str__(self):
        return self.NomEvenement


class Chantre(models.Model):
    Nom = models.CharField(max_length=100, blank=False)
    Phone_number = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(blank=False, upload_to='chamtrepictures', null=False)

    class Meta:
        verbose_name = 'Chantre'

    def __str__(self):
        return self.Nom
    

class Croyant(models.Model):
    nom = models.CharField("Nom et Prénom", max_length=100)
    photo_profil = models.ImageField("Photo de profil (Bulle)", upload_to='croyants/profils/')
    adresse = models.CharField("Adresse", max_length=200)
    
    # On permet null=True au cas où la date exacte est oubliée
    date_conversion = models.DateField("Date de conversion", null=True, blank=True)
    
    etat_civil = models.CharField("État Civil", max_length=100, help_text="Ex: Marié, 3 enfants")
    ambitions = models.TextField("Sa prière / Ses ambitions")
    pourquoi_wmb = models.TextField("Pourquoi WMB Tabernacle ?")
    
    # Pour savoir quand l'article a été publié
    date_publication = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fidèle / Croyant"
        verbose_name_plural = "Les Fidèles (Connaissons-nous)"
        ordering = ['-date_publication'] # Les plus récents en premier

    def __str__(self):
        return self.nom

class PhotoSouvenir(models.Model):
    # Le lien vers le croyant (Clé étrangère)
    croyant = models.ForeignKey(Croyant, on_delete=models.CASCADE, related_name='album')
    image = models.ImageField(upload_to='croyants/album/')
    legende = models.CharField("Légende (optionnel)", max_length=100, blank=True)

    def __str__(self):
        return f"Photo de {self.croyant.nom}"
    

class ClasseEcodim(models.Model):
    nom = models.CharField("Nom de la classe", max_length=100) # Ex: Les Agneaux
    tranche_age = models.CharField("Tranche d'âge", max_length=50) # Ex: 3-6 ans
    description = models.TextField("Ce qu'ils apprennent")
    image = models.ImageField(upload_to='ecodim/classes/')
    couleur_theme = models.CharField("Couleur (Hex ou Tailwind)", max_length=20, default="bg-blue-500")

    def __str__(self):
        return self.nom

class Moniteur(models.Model):
    nom = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default="Moniteur / Monitrice")
    photo = models.ImageField(upload_to='ecodim/moniteurs/')

    def __str__(self):
        return self.nom
