from django.shortcuts import render
from sermons.models import Theme

# Create your views here.
def ViewTheme(request):
    Themes = Theme.objects.all()
    return render(request, 'ViewTheme.html', {'themes': Themes})