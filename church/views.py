from django.shortcuts import render

from sermons.models import Sermons


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
