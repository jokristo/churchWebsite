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
