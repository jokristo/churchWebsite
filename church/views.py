import random

from django.http import Http404
from django.shortcuts import render

from actualites.models import Article
from actualites.services import annotate_articles_likes
from sermons.models import Sermons


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)


def custom_403(request, exception):
    return render(request, 'errors/403.html', status=403)


def custom_400(request, exception):
    return render(request, 'errors/400.html', status=400)


def test_404(request):
    """Vue pour tester la page 404 (visiter /erreur-404/)"""
    raise Http404("Page de test")


def index(request):
    published = Article.objects.filter(est_publie=True)
    article_recent = published.first()
    article_second = None
    second_is_vedette = False

    if article_recent:
        vedette = published.filter(en_vedette=True).first()
        if vedette and vedette.pk != article_recent.pk:
            article_second = vedette
            second_is_vedette = True
        else:
            others = published.exclude(pk=article_recent.pk)
            n = others.count()
            if n:
                article_second = others[random.randint(0, n - 1)]

    home_articles = [a for a in (article_recent, article_second) if a]
    annotate_articles_likes(request, home_articles)

    return render(
        request,
        'home.html',
        {
            'article_recent': article_recent,
            'article_second': article_second,
            'second_is_vedette': second_is_vedette,
        },
    )


def sermons(request, *args, **kwargs):
    sermon = Sermons.objects.all()
    # imgsermon = Sermons.objects.get()
    if request.method == "GET":
        titre = request.GET.get('recherche')
        if titre is not None:
            sermon = Sermons.objects.filter(titre__icontains=titre)

    return render(request, 'sermons.html', context={"dba": sermon})


def chantre(request):
    return render(request, 'chantre.html')
