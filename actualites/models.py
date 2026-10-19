from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit

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
    image_couverture = ProcessedImageField(
        verbose_name="Image de couverture",
        upload_to='blog/couvertures/',
        processors=[ResizeToFit(800, 450)],
        format='WEBP',
        options={'quality': 82},
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


class ArticleLike(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name="Article",
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='article_likes',
        verbose_name="Utilisateur",
    )
    session_key = models.CharField(
        "Clé de session",
        max_length=40,
        blank=True,
        db_index=True,
    )
    ip_hash = models.CharField(
        "Empreinte IP",
        max_length=64,
        blank=True,
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Like d'article"
        verbose_name_plural = "Likes d'articles"
        constraints = [
            models.UniqueConstraint(
                fields=['article', 'utilisateur'],
                condition=models.Q(utilisateur__isnull=False),
                name='unique_article_like_user',
            ),
            models.UniqueConstraint(
                fields=['article', 'session_key'],
                condition=models.Q(utilisateur__isnull=True),
                name='unique_article_like_session',
            ),
        ]

    def __str__(self):
        who = self.utilisateur or self.session_key[:8]
        return f"Like — {self.article.titre} ({who})"


class Commentaire(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Article",
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commentaires_articles',
        verbose_name="Utilisateur",
    )
    nom = models.CharField("Nom", max_length=100)
    email = models.EmailField("E-mail", blank=True)
    contenu = models.TextField("Commentaire", max_length=2000)
    est_approuve = models.BooleanField("Approuvé", default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} — {self.article.titre}"

    @property
    def auteur_affiche(self):
        if self.utilisateur:
            return self.utilisateur.get_full_name() or self.utilisateur.username
        return self.nom
