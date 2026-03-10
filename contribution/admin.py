from django.contrib import admin
from .models import EvolutionConstruction, Contribution

@admin.register(EvolutionConstruction)
class EvolutionAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_travaux', 'date_publication')
    list_filter = ('date_travaux',)

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('get_nom', 'montant', 'date_don', 'transaction_id')
    search_fields = ('nom_donateur', 'transaction_id')
    readonly_fields = ('date_don',)  # transaction_id modifiable à la création pour ajouts manuels

    def get_nom(self, obj):
        return obj.nom_donateur if obj.nom_donateur else "Anonyme"
    get_nom.short_description = 'Donateur'