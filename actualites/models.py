from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class Categorie(models.Model):
    nom = models.CharField("Catégorie", max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['nom']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Article(models.Model):
    titre = models.CharField("Titre", max_length=200)
    slug = models.SlugField("Slug (URL)", max_length=200, unique=True, blank=True)
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name="Catégorie"
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Auteur"
    )
    image_couverture = models.ImageField(
        "Image de couverture",
        upload_to='blog/couvertures/',
        blank=True,
        null=True
    )
    resume = models.TextField(
        "Résumé",
        max_length=300,
        help_text="Courte description affichée sur la liste (max 300 caractères)"
    )
    contenu = models.TextField("Contenu de l'article")
    date_evenement = models.DateField(
        "Date de l'événement (optionnel)",
        null=True,
        blank=True,
        help_text="Remplir uniquement si l'article annonce un événement"
    )
    est_publie = models.BooleanField("Publié", default=False)
    en_vedette = models.BooleanField("En vedette", default=False)
    date_publication = models.DateTimeField("Date de publication", auto_now_add=True)
    date_modification = models.DateTimeField("Dernière modification", auto_now=True)

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-date_publication']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre
