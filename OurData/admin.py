from django.contrib import admin
from OurData.models import Temoignages, Evenements, Chantre

# Register your models here.
#admin.site.register(Temoignages)
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


@admin.register(Evenements)
class EvenementAdmin(admin.ModelAdmin):
    list_display = [
        "NomEvenement",
        "Date"
    ]

    search_fields = ('NomEvenement',)


admin.site.register(Chantre)
