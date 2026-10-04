import random

from django.shortcuts import render

from actualites.models import Article
from actualites.services import annotate_articles_likes
from sermons.models import Orateur, Sermons, Theme


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)


def custom_403(request, exception):
    return render(request, 'errors/403.html', status=403)


def custom_400(request, exception):
    return render(request, 'errors/400.html', status=400)


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
    qs = Sermons.objects.select_related('orateur', 'Theme').order_by('-date')
    recherche = (request.GET.get('recherche') or '').strip()
    theme_id = request.GET.get('theme') or ''
    orateur_id = request.GET.get('orateur') or ''

    if recherche:
        qs = qs.filter(titre__icontains=recherche)
    if theme_id.isdigit():
        qs = qs.filter(Theme_id=int(theme_id))
    else:
        theme_id = ''
    if orateur_id.isdigit():
        qs = qs.filter(orateur_id=int(orateur_id))
    else:
        orateur_id = ''

    has_filters = bool(recherche or theme_id or orateur_id)
    sermon_count = qs.count()

    return render(
        request,
        'sermons.html',
        {
            'dba': qs,
            'themes': Theme.objects.order_by('NomTheme'),
            'orateurs': Orateur.objects.order_by('Noms'),
            'recherche': recherche,
            'theme_actif': theme_id,
            'orateur_actif': orateur_id,
            'has_filters': has_filters,
            'sermon_count': sermon_count,
        },
    )

