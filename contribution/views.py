from django.shortcuts import render
from .models import EvolutionConstruction, Contribution

def page_contribution(request):
    photos = EvolutionConstruction.objects.all()
    # On récupère les 50 derniers dons pour le scroll
    dons = Contribution.objects.all()[:50] 
    
    # On calcule les années disponibles pour le filtre
    annees = photos.dates('date_travaux', 'year', order='DESC')
    
    return render(request, 'contribution.html', {
        'photos': photos,
        'dons': dons,
        'annees': annees
    })
