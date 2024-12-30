from django.db import models
from OurData.models import Ministre
from django.utils.timezone import now

# Create your models here.
class Orateur(models.Model):
    Noms = models.CharField(max_length=100, blank=False)
    Provenance = models.CharField(max_length = 50, blank = True, null = True)


    def __str__(self):
        return self.Noms

class Theme(models.Model):
    NomTheme = models.CharField(max_length=100, blank = False)
    ThemeDescription = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, upload_to='sermons')
    ministre = models.ForeignKey(Ministre, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.NomTheme
    
class Sermons(models.Model):
    titre = models.CharField(max_length=100, blank=False)
    image = models.ImageField(blank=True, upload_to='sermons')
    orateur = models.ForeignKey(Orateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=now, null=True)
    lien = models.URLField(max_length=200, blank=True, null=True)
    audio = models.FileField(blank=True, upload_to='audio')
    Theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)



    class Meta:
        verbose_name = 'Sermon'


    def __str__(self):
        return self.titre


