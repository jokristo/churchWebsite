from django.http import Http404
from django.shortcuts import render

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
    return render(request, 'home.html')


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
