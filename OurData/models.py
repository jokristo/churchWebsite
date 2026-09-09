from django.db import models
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill, ResizeToFit
from church.utils.audio import AudioCompressionMixin


# Create your models here.
class Ministre(models.Model):
    FONCTION_CHOICES = [
        ('titulaire', 'Pasteur titulaire'),
        ('associe', 'Pasteur associé'),
        ('evangeliste', 'Évangéliste'),
        ('ministre', 'Ministre de la Parole'),
        ('invite', 'Invité'),
    ]

    Nom = models.CharField(max_length=100, blank=False)
    photo = ProcessedImageField(
        blank=True, upload_to='ministrespictures',
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )
    contact = models.CharField(max_length=25, blank=True)
    fonction = models.CharField(max_length=20, choices=FONCTION_CHOICES, blank=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Ministre'
        ordering = ['ordre', 'Nom']

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
    photo = ProcessedImageField(
        blank=True, upload_to='officielpictures',
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )
    categorieOfficiel = models.ForeignKey(CategorieOfficiel, on_delete=models.SET_NULL, null=True )

    class Meta:
        verbose_name = 'Officiel'

    def __str__(self):
        return self.Nom


class Temoignages(AudioCompressionMixin, models.Model):
    NomDuCroyant = models.CharField(max_length=100, blank=True)
    Audio = models.FileField(blank=True, upload_to='audio', null=True)
    Description = models.TextField(blank=False)
    photo = ProcessedImageField(
        blank=True, upload_to='temoignagespictures', null=True,
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )
    is_Approuve = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Temoignage'

    def __str__(self):
        return self.NomDuCroyant

    audio_field_name = 'Audio'


class Chantre(models.Model):
    Nom = models.CharField(max_length=100, blank=False)
    Phone_number = models.CharField(max_length=100, blank=True)
    photo = ProcessedImageField(
        blank=False, upload_to='chamtrepictures', null=False,
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )

    class Meta:
        verbose_name = 'Chantre'

    def __str__(self):
        return self.Nom
    

class Croyant(models.Model):
    nom = models.CharField("Nom et Prénom", max_length=100)
    photo_profil = ProcessedImageField(
        verbose_name="Photo de profil (Bulle)", upload_to='croyants/profils/',
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )
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
    image = ProcessedImageField(
        upload_to='croyants/album/',
        processors=[ResizeToFit(800, 600)],
        format='WEBP', options={'quality': 82}
    )
    legende = models.CharField("Légende (optionnel)", max_length=100, blank=True)

    def __str__(self):
        return f"Photo de {self.croyant.nom}"
    

class ClasseEcodim(models.Model):
    nom = models.CharField("Nom de la classe", max_length=100) # Ex: Les Agneaux
    tranche_age = models.CharField("Tranche d'âge", max_length=50) # Ex: 3-6 ans
    description = models.TextField("Ce qu'ils apprennent")
    image = ProcessedImageField(
        upload_to='ecodim/classes/',
        processors=[ResizeToFit(600, 400)],
        format='WEBP', options={'quality': 80}
    )
    couleur_theme = models.CharField("Couleur (Hex ou Tailwind)", max_length=20, default="bg-blue-500")

    def __str__(self):
        return self.nom

class Moniteur(models.Model):
    nom = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default="Moniteur / Monitrice")
    photo = ProcessedImageField(
        upload_to='ecodim/moniteurs/',
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Encadreur Écodim"
        verbose_name_plural = "Encadreurs Écodim"
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class MembreMedia(models.Model):
    """Membre de l'équipe Média & Presse."""
    nom = models.CharField("Nom complet", max_length=100)
    role = models.CharField("Rôle / Titre", max_length=100)  # Ex: Chef de la communication
    description = models.TextField("Description", blank=True)
    photo = ProcessedImageField(
        verbose_name="Photo", upload_to='media_presse/',
        blank=True, null=True,
        processors=[ResizeToFill(400, 400)],
        format='WEBP', options={'quality': 82}
    )
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Membre Média & Presse"
        verbose_name_plural = "Membres Média & Presse"
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"{self.nom} - {self.role}"
