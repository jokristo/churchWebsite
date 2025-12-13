from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
# from OurData.forms import TemoignageForm
from OurData.forms import TemoignageForm
from OurData.models import  Ministre, Evenements, Temoignages, Chantre, CategorieOfficiel, Officiel




def categorieOfficiel(request):
    categories = CategorieOfficiel.objects.all()
    
    return render(request, 'categorieofficiel.html', {"categories":categories})


def officiels(request, categorie_id):
     #recuperation de la categorie en fonction de l'id
    categorieOfficiel = get_object_or_404(CategorieOfficiel, id=categorie_id)
    #liason des officiels aux categories
    officiels = Officiel.objects.filter(categorieOfficiel=categorieOfficiel)

    return render(request, "officiel.html", context={"offi": officiels, "categories":categorieOfficiel})


def ministres(request):
    ministre = Ministre.objects.all()
    # imgmin = Ministre.objects.get()
    return render(request, 'ministre.html', context={"ministres": ministre})


def temoignages(request):
    if request.method == "POST":
        formtemoin = TemoignageForm(request.POST, request.FILES)
        if formtemoin.is_valid():
            formtemoin.save()
            return redirect('temoignagecontent') 
    else:
        formtemoin = TemoignageForm()

    return render(request, "temoignage.html", {"form": formtemoin})

def temoin(request):
    temoignage2 = Temoignages.objects.filter(is_Approuve = "True")
    return render(request, "temoignage2.html", {"datatemoignages": temoignage2})


def Evenement(request):
    dataEvent = Evenements.objects.all()
    return render(request, "Evenement.html", {"events": dataEvent})


def chantre(request):
    chantres = Chantre.objects.all()
    return render(request, "chantre.html", {"chantres": chantres})

# Dans views.py

from django.shortcuts import render


def media_presse(request):
    """
    Affiche la page de l'équipe média et presse.
    Le contenu sera stylisé en Tailwind/JS dans le template.
    """
    context = {
        'page_title': "Équipe Média & Presse",
    }
    return render(request, 'media_presse.html', context)


def biographie_pasteur(request):
    """
    Affiche la page de biographie statique d'un pasteur.
    """
    context = {
        'page_title': "Biographie du Pasteur Principal",
    }
    return render(request, 'biographie_pasteur.html', context)
