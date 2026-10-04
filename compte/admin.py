from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from compte.models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """UserAdmin gère correctement les mots de passe (hachage, formulaire dédié)."""
