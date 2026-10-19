from django.contrib import admin
from .models import Categorie, Article, ArticleLike, Commentaire


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'slug']
    prepopulated_fields = {'slug': ('nom',)}
    search_fields = ('nom',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'auteur', 'est_publie', 'en_vedette', 'date_publication']
    list_filter = ('est_publie', 'en_vedette', 'categorie')
    list_editable = ['est_publie', 'en_vedette']
    search_fields = ('titre', 'resume', 'contenu')
    prepopulated_fields = {'slug': ('titre',)}
    readonly_fields = ('date_publication', 'date_modification')
    fieldsets = (
        ('Contenu', {
            'fields': ('titre', 'slug', 'categorie', 'auteur', 'image_couverture', 'resume', 'contenu')
        }),
        ('Événement lié', {
            'fields': ('date_evenement',),
            'classes': ('collapse',),
        }),
        ('Publication', {
            'fields': ('est_publie', 'en_vedette', 'date_publication', 'date_modification')
        }),
    )


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ['article', 'utilisateur', 'session_key', 'date_creation']
    list_filter = ('date_creation',)
    search_fields = ('article__titre', 'utilisateur__username', 'session_key')
    readonly_fields = ('date_creation',)


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['apercu', 'nom', 'article', 'est_approuve', 'date_creation']
    list_display_links = ['apercu']
    list_filter = ('est_approuve', 'date_creation', 'article')
    list_editable = ['est_approuve']
    search_fields = ('nom', 'email', 'contenu', 'article__titre')
    readonly_fields = ('date_creation',)
    # Les commentaires en attente apparaissent en premier.
    ordering = ('est_approuve', '-date_creation')
    actions = ['approuver', 'desapprouver']

    @admin.display(description="Commentaire")
    def apercu(self, obj):
        texte = obj.contenu or ''
        return texte[:80] + ('…' if len(texte) > 80 else '')

    @admin.action(description="Approuver les commentaires sélectionnés")
    def approuver(self, request, queryset):
        n = queryset.update(est_approuve=True)
        self.message_user(request, f"{n} commentaire(s) approuvé(s).")

    @admin.action(description="Masquer les commentaires sélectionnés")
    def desapprouver(self, request, queryset):
        n = queryset.update(est_approuve=False)
        self.message_user(request, f"{n} commentaire(s) masqué(s).")
