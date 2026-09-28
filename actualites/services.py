import hashlib

from django.db.models import Count

from .models import ArticleLike


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def get_ip_hash(request):
    return hashlib.sha256(get_client_ip(request).encode()).hexdigest()[:32]


def get_liked_article_ids(request, article_ids):
    if not article_ids:
        return set()

    qs = ArticleLike.objects.filter(article_id__in=article_ids)
    if request.user.is_authenticated:
        return set(qs.filter(utilisateur=request.user).values_list('article_id', flat=True))

    session_key = ensure_session_key(request)
    return set(
        qs.filter(utilisateur__isnull=True, session_key=session_key).values_list('article_id', flat=True)
    )


def get_like_counts(article_ids):
    if not article_ids:
        return {}
    return dict(
        ArticleLike.objects.filter(article_id__in=article_ids)
        .values('article_id')
        .annotate(count=Count('id'))
        .values_list('article_id', 'count')
    )


def annotate_articles_likes(request, articles):
    article_list = list(articles)
    ids = [a.pk for a in article_list]
    counts = get_like_counts(ids)
    liked_ids = get_liked_article_ids(request, ids)
    for article in article_list:
        article.like_count = counts.get(article.pk, 0)
        article.user_liked = article.pk in liked_ids
    return article_list


def toggle_article_like(request, article):
    if request.user.is_authenticated:
        like, created = ArticleLike.objects.get_or_create(
            article=article,
            utilisateur=request.user,
            defaults={'ip_hash': get_ip_hash(request)},
        )
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
    else:
        session_key = ensure_session_key(request)
        like, created = ArticleLike.objects.get_or_create(
            article=article,
            session_key=session_key,
            utilisateur=None,
            defaults={'ip_hash': get_ip_hash(request)},
        )
        if not created:
            like.delete()
            liked = False
        else:
            liked = True

    count = ArticleLike.objects.filter(article=article).count()
    return liked, count
