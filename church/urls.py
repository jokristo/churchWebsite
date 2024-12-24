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
from django.urls import path, include
from OurData.views import officiels, ministres, temoignages, Evenement, temoin, chantre
from chat.views import chat, send_message
from compte.views import Sign, login_user, logout_user
from .views import index, sermons
from sermons.views import ViewTheme
from church import settings

# checkview, chat, room, send, getMessages,
urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', index, name="home"),
                  path('sermons/', sermons, name="sermons"),
                  path('offi/', officiels, name="officiels"),
                  path('ministre/', ministres, name="ministres"),
                  path('temoignage/', temoignages, name="temoignages"),
                  path('event/', Evenement, name='event'),
                  path("temoignagecontent/", temoin, name="temoignagecontent"),
                  path("ViewTheme/", ViewTheme, name="ViewTheme"),
                  path("chantre/", chantre, name="chantre")
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

