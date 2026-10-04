"""
URL configuration for church project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from OurData.views import ministres, temoignages, temoin, chantre, categorieOfficiel, officiels, biographie_pasteur, media_presse, connaissons_nous_liste, connaissons_nous_detail, ecodim_view
from actualites.views import blog_liste, blog_detail, toggle_like
from .views import index, sermons
from sermons.views import ViewTheme, SermonByTheme, ThemeByMinister
from contribution.views import page_contribution
from django.conf import settings
from church.views import custom_404, custom_500, custom_403, custom_400

handler404 = custom_404
handler500 = custom_500
handler403 = custom_403
handler400 = custom_400

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', index, name="home"),
                  path('sermons/', sermons, name="sermons"),
                  path('offi/<int:categorie_id>/', officiels, name="officiels"),
                  path('ministre/', ministres, name="ministres"),
                  path('temoignage/', temoignages, name="temoignages"),
                  path('blog/', blog_liste, name='blog'),
                  path('blog/<slug:slug>/like/', toggle_like, name='blog_toggle_like'),
                  path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
                  path("temoignagecontent/", temoin, name="temoignagecontent"),
                  #voir tous le theme
                  path("ViewTheme/", ViewTheme, name="ViewTheme"),
                  #vue pour voir les sermons en foction du theme
                  path("SermonByTheme/<int:theme_id>/", SermonByTheme, name="SermonByTheme"),
                  #vue pour voir les sermons en fonction du ministre
                  path("themeByMinister/<int:ministre_id>/", ThemeByMinister, name="ThemeByMinister"),
                  #categories des officiels
                  path("cateOffi/", categorieOfficiel, name='categorieOfficiel'),
                  #vue pour voir tous le chantres
                  path("chantre/", chantre, name="chantre"),
                  path('media/', media_presse, name='media_presse'),
                  path('biographie/', biographie_pasteur, name='biographie_pasteur'),
                  path('connaissons-nous/', connaissons_nous_liste, name='connaissons_nous_liste'),
                  # <int:id_croyant> permet de capturer le numéro (1, 2, etc.)
                  path('connaissons-nous/<int:id_croyant>/', connaissons_nous_detail, name='connaissons_nous_detail'),
                  path('ecodim/', ecodim_view, name='ecodim'),
                  path('contribution/', page_contribution, name='contribution'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

