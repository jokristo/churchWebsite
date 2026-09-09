from django.db import models
from OurData.models import Ministre
from django.utils.timezone import now
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from church.utils.audio import AudioCompressionMixin

# Create your models here.
class Orateur(models.Model):
    Noms = models.CharField(max_length=100, blank=False)
    Provenance = models.CharField(max_length = 50, blank = True, null = True)
    ministre = models.ForeignKey(
        Ministre, on_delete=models.SET_NULL, null=True, blank=True, related_name='orateurs'
    )

    def __str__(self):
        return self.Noms

class Theme(models.Model):
    NomTheme = models.CharField(max_length=100, blank = False)
    ThemeDescription = models.TextField(blank=True, null=True)
    image = ProcessedImageField(
        blank=True, upload_to='sermons',
        processors=[ResizeToFit(700, 400)],
        format='WEBP',
        options={'quality': 80}
    )
    ministre = models.ForeignKey(Ministre, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.NomTheme
    
class Sermons(AudioCompressionMixin, models.Model):
    titre = models.CharField(max_length=100, blank=False)
    image = ProcessedImageField(
        blank=True, upload_to='sermons',
        processors=[ResizeToFit(700, 400)],
        format='WEBP',
        options={'quality': 80}
    )
    orateur = models.ForeignKey(Orateur, on_delete=models.SET_NULL, null=True, related_name='sermons')
    date = models.DateTimeField(default=now, null=True)
    lien = models.URLField(max_length=200, blank=True, null=True)
    audio = models.FileField(blank=True, upload_to='audio')
    Theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)



    class Meta:
        verbose_name = 'Sermon'


    def __str__(self):
        return self.titre


