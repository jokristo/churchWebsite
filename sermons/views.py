from django.shortcuts import render, get_object_or_404
from sermons.models import Theme, Sermons
from OurData.models import Ministre

# Create your views here.
def SermonByTheme(request, theme_id):
    #recuperation du theme
    theme = get_object_or_404(Theme, id=theme_id)
    #print(theme)
    #recuperation des sermons de ce theme
    sermons = Sermons.objects.filter(Theme=theme)
    #print(sermons)
    return render(request, 'SermonByTheme.html', {'theme': theme, 'sermons': sermons})


def ViewTheme(request):
    Themes = Theme.objects.all()
    return render(request, 'ViewTheme.html', {'themes': Themes})


def ThemeByMinister(request, ministre_id):
    #recuparation du ministre
    ministre = get_object_or_404(Ministre, ministre_id)
    #recuperation des theme lier à lui
    themes = Theme.objects.filtre(ministre=ministre)
    return render(request, 'themeByMinister.html', {'ministre': ministre, 'themes': themes})

