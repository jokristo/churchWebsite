from django.shortcuts import render
from .models import EvolutionConstruction, Contribution
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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

# API pour enregistrer le don après succès PayPal
@csrf_exempt
def enregistrer_don(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Contribution.objects.create(
            nom_donateur=data.get('nom', ''), # Vide si anonyme
            montant=data.get('montant'),
            transaction_id=data.get('transaction_id')
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)