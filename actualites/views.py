from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import CommentaireForm
from .models import Article, Categorie, Commentaire
from .services import annotate_articles_likes, get_ip_hash, toggle_article_like

# Délai minimum (en secondes) entre deux commentaires depuis la même adresse IP.
DELAI_ENTRE_COMMENTAIRES = 60
MESSAGE_EN_ATTENTE = (
    "Merci ! Votre commentaire a bien été reçu. "
    "Il sera visible après validation par l'équipe."
)


def blog_liste(request):
    categorie_slug = request.GET.get('categorie')
    articles = Article.objects.filter(est_publie=True).select_related('categorie', 'auteur')
    categories = Categorie.objects.all()
    categorie_active = None

    if categorie_slug:
        categorie_active = get_object_or_404(Categorie, slug=categorie_slug)
        articles = articles.filter(categorie=categorie_active)

    articles_vedette = list(articles.filter(en_vedette=True)[:2])
    articles_liste = list(
        articles.exclude(en_vedette=True) if articles_vedette else articles
    )

    annotate_articles_likes(request, articles_vedette)
    annotate_articles_likes(request, articles_liste)

    return render(request, 'blog/blog_liste.html', {
        'articles': articles_liste,
        'articles_vedette': articles_vedette,
        'categories': categories,
        'categorie_active': categorie_active,
    })


def blog_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related('categorie', 'auteur'),
        slug=slug,
        est_publie=True,
    )
    articles_recents = list(
        Article.objects.filter(est_publie=True)
        .exclude(pk=article.pk)
        .select_related('categorie')[:3]
    )
    annotate_articles_likes(request, [article] + articles_recents)

    commentaires = article.commentaires.filter(est_approuve=True).select_related('utilisateur')
    comment_form = CommentaireForm(user=request.user)

    if request.method == 'POST' and 'commentaire' in request.POST:
        comment_form = CommentaireForm(request.POST, user=request.user)
        if comment_form.is_valid():
            # Robot détecté : on fait semblant d'accepter, sans rien enregistrer.
            if comment_form.est_spam():
                messages.success(request, MESSAGE_EN_ATTENTE)
                return redirect('blog_detail', slug=slug)

            cle_limite = f"commentaire-ip-{get_ip_hash(request)}"
            if cache.get(cle_limite) and not request.user.is_staff:
                messages.error(
                    request,
                    "Vous venez déjà de commenter. Merci de patienter une minute avant de réessayer.",
                )
                return redirect('blog_detail', slug=slug)

            commentaire = comment_form.save(commit=False)
            commentaire.article = article
            if request.user.is_authenticated:
                commentaire.utilisateur = request.user
            # Les commentaires de l'équipe (staff) sont publiés directement,
            # ceux des visiteurs attendent une validation dans l'admin.
            commentaire.est_approuve = request.user.is_staff
            commentaire.save()
            cache.set(cle_limite, True, DELAI_ENTRE_COMMENTAIRES)

            if commentaire.est_approuve:
                messages.success(request, "Votre commentaire a été publié. Merci !")
            else:
                messages.success(request, MESSAGE_EN_ATTENTE)
            return redirect('blog_detail', slug=slug)

    return render(request, 'blog/blog_detail.html', {
        'article': article,
        'articles_recents': articles_recents,
        'commentaires': commentaires,
        'comment_form': comment_form,
    })


@require_POST
def toggle_like(request, slug):
    article = get_object_or_404(Article, slug=slug, est_publie=True)
    liked, count = toggle_article_like(request, article)
    return JsonResponse({'liked': liked, 'count': count})
