from django.contrib import admin
from OurData.models import ClasseEcodim, Croyant, Moniteur, Temoignages, Chantre, CategorieOfficiel, PhotoSouvenir, MembreMedia

# Register your models here.
admin.site.register(CategorieOfficiel)

@admin.register(Temoignages)
class TemoignageAdmin(admin.ModelAdmin):
    list_display = [
        "NomDuCroyant",
        "Description",
        "is_Approuve",
        "photo",
        "Audio",
    ]
    search_fields = ('NomDuCroyant',)



admin.site.register(Chantre)


class PhotoSouvenirInline(admin.TabularInline):
    model = PhotoSouvenir
    extra = 1 # Affiche 1 ligne vide par défaut pour ajouter une photo

class CroyantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_conversion', 'adresse', 'date_publication')
    inlines = [PhotoSouvenirInline] # On attache l'album ici

admin.site.register(Croyant, CroyantAdmin)

@admin.register(ClasseEcodim)
class ClasseEcodimAdmin(admin.ModelAdmin):
    list_display = [
        "nom",
        "tranche_age",
        "description",
        "image"
    ]

    search_fields = ('nom',)

@admin.register(Moniteur)
class MoniteurAdmin(admin.ModelAdmin):
    list_display = ["nom", "role", "ordre", "photo"]
    list_editable = ["ordre"]
    search_fields = ('nom', 'role')


@admin.register(MembreMedia)
class MembreMediaAdmin(admin.ModelAdmin):
    list_display = ["nom", "role", "ordre", "photo"]
    list_editable = ["ordre"]
    search_fields = ('nom', 'role')