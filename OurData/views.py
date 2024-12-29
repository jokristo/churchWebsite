from django.shortcuts import render

# Create your views here.
# from OurData.forms import TemoignageForm
from OurData.forms import TemoignageForm
from OurData.models import Officiel, Ministre, Evenements, Temoignages, Chantre


def officiels(request):
    officiel = Officiel.objects.all()

    return render(request, "officiel.html", context={"offi": officiel})


def ministres(request):
    ministre = Ministre.objects.all()
    # imgmin = Ministre.objects.get()
    return render(request, 'ministre.html', context={"ministres": ministre})


def temoignages(request):
    if request.method == "POST":
        formtemoin = TemoignageForm(request.POST, request.FILES)
        if formtemoin.is_valid():
            formtemoin.save()
    else:
        formtemoin = TemoignageForm()

    return render(request, "temoignage.html", {"formute": formtemoin})


def temoin(request):
    temoignage2 = Temoignages.objects.filter(is_Approuve = "True")
    return render(request, "temoignage2.html", {"datatemoignages": temoignage2})


def Evenement(request):
    dataEvent = Evenements.objects.all()
    return render(request, "Evenement.html", {"events": dataEvent})


def chantre(request):
    chantres = Chantre.objects.all()
    return render(request, "chantre.html", {"chantres": chantres})
