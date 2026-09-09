from django.db.models import Count, Prefetch
from django.shortcuts import render, get_object_or_404, redirect, Http404
# Create your views here.
# from OurData.forms import TemoignageForm
from OurData.forms import TemoignageForm
from OurData.models import Ministre, Temoignages, Chantre, CategorieOfficiel, Officiel, Croyant, ClasseEcodim, Moniteur, MembreMedia
from sermons.models import Orateur




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
    qs = Ministre.objects.annotate(
        sermon_count=Count('orateurs__sermons', distinct=True)
    ).prefetch_related(Prefetch('orateurs', queryset=Orateur.objects.order_by('id')))

    recherche = (request.GET.get('recherche') or '').strip()
    fonction = request.GET.get('fonction') or ''
    predications = request.GET.get('predications') or ''

    fonctions_valides = {key for key, _ in Ministre.FONCTION_CHOICES}
    if fonction not in fonctions_valides:
        fonction = ''
    if predications not in {'avec', 'sans'}:
        predications = ''

    if recherche:
        qs = qs.filter(Nom__icontains=recherche)
    if fonction:
        qs = qs.filter(fonction=fonction)
    if predications == 'avec':
        qs = qs.filter(sermon_count__gt=0)
    elif predications == 'sans':
        qs = qs.filter(sermon_count=0)

    qs = qs.order_by('ordre', 'Nom')
    has_filters = bool(recherche or fonction or predications)

    return render(
        request,
        'ministre.html',
        {
            'ministres': qs,
            'recherche': recherche,
            'fonction_active': fonction,
            'predications_actives': predications,
            'fonctions': Ministre.FONCTION_CHOICES,
            'has_filters': has_filters,
            'ministre_count': qs.count(),
        },
    )


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



def chantre(request):
    chantres = Chantre.objects.all()
    return render(request, "chantre.html", {"chantres": chantres})

# Dans views.py

from django.shortcuts import render


def media_presse(request):
    """
    Affiche la page de l'équipe média et presse.
    Les membres sont gérés depuis l'admin Django.
    """
    membres = MembreMedia.objects.all()
    return render(request, 'media_presse.html', {
        'page_title': "Équipe Média & Presse",
        'membres': membres,
    })


def biographie_pasteur(request):
    """
    Affiche la page de biographie statique d'un pasteur.
    """
    context = {
        'page_title': "Biographie du Pasteur Principal",
    }
    return render(request, 'biographie_pasteur.html', context)



def connaissons_nous_liste(request):
    croyants = Croyant.objects.all()
    return render(request, "connaissons_nous_liste.html", {"croyants": croyants})

# --- VUE 2 : LE DÉTAIL ---
def connaissons_nous_detail(request, id_croyant):

    fidele = get_object_or_404(Croyant.objects.prefetch_related('album'), pk=id_croyant)
    
    return render(request, "connaissons_nous_detail.html", {"fidele": fidele})

def ecodim_view(request):
    classes = ClasseEcodim.objects.all()
    moniteurs = Moniteur.objects.all()
    return render(request, 'ecodim.html', {
        'classes': classes,
        'moniteurs': moniteurs
    })
