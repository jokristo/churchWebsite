from django.contrib import admin
from sermons.models import Sermons
from sermons.models import Orateur
from OurData.models import Ministre
from OurData.models import Officiel



# Register your models here.
@admin.register(Sermons)
class SermonAdmin(admin.ModelAdmin):
    list_display = [
        "titre",
        "orateur",
        "date",
        "lien",
        "audio"
    ]

    search_fields = ('titre',)



@admin.register(Orateur)
class OrateurAdmin(admin.ModelAdmin):
    pass
    search_fields = ('titre',)

@admin.register(Ministre)
class MinistreAdmin(admin.ModelAdmin):
    list_display = [
        "Nom",
        "contact",
    ]

    search_fields=('Nom',)

@admin.register(Officiel)
class MinistreAdmin(admin.ModelAdmin):
    list_display = [
        "Nom",
        "contact",
        "fonction"
    ]

    search_fields=('Nom','fonction')