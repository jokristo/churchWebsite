from django.shortcuts import render, get_object_or_404
from .models import Article, Categorie


def blog_liste(request):
    categorie_slug = request.GET.get('categorie')
    articles = Article.objects.filter(est_publie=True)
    categories = Categorie.objects.all()
    categorie_active = None

    if categorie_slug:
        categorie_active = get_object_or_404(Categorie, slug=categorie_slug)
        articles = articles.filter(categorie=categorie_active)

    articles_vedette = articles.filter(en_vedette=True)[:2]
    articles_liste = articles.exclude(en_vedette=True) if articles_vedette.exists() else articles

    return render(request, 'blog/blog_liste.html', {
        'articles': articles_liste,
        'articles_vedette': articles_vedette,
        'categories': categories,
        'categorie_active': categorie_active,
    })


def blog_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, est_publie=True)
    articles_recents = Article.objects.filter(est_publie=True).exclude(pk=article.pk)[:3]

    return render(request, 'blog/blog_detail.html', {
        'article': article,
        'articles_recents': articles_recents,
    })
