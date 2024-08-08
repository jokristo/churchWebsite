from django.db import models


# Create your models here.
class Orateur(models.Model):
    nom = models.CharField(max_length=100, blank=False)


    def __str__(self):
        return self.nom


class Sermons(models.Model):
    titre = models.CharField(max_length=100, blank=False)
    image = models.ImageField(blank=True, upload_to='sermons')
    orateur = models.ForeignKey(Orateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(blank=True)
    lien = models.URLField(max_length=200, blank=True, null=True)
    audio = models.FileField(blank=True, upload_to='audio')



    class Meta:
        verbose_name = 'Sermon'


    def __str__(self):
        return self.titre


