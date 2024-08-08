from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from compte.models import Utilisateur

"""def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            return render(request, "signup.html", {"error": "les mots de passes ne correspondent pas"})
        Utilisateur.objects.create_user(username=username, password=password1)
        return HttpResponse(f"bienvenue {{username}}")

    return render(request, 'signup.html')
"""


def Sign(request, *args, **kwargs):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = Utilisateur.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('login')
    return render(request, 'compte.html')


def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=username, email=email, password=password)
        if user is not None:
            login(request, user)
            request.session['username'] = user.username  # Stockez le nom d'utilisateur dans la session
            return redirect('chat')  # Redirigez vers la vue du chat après la connexion
        else:
            # Gérez le cas où l'authentification échoue
            return render(request, 'login.html', {'error_message': 'Identifiants invalides'})

    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    return redirect('home')
