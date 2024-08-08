# views.py
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect

from compte.models import Utilisateur
from .models import Message, Messa
from django.contrib.auth.decorators import login_required
import json


@login_required
def chat(request):
    messages = Message.objects.all().order_by('-timestamp')[:40]  # Obtenez les 50 derniers messages
    return render(request, 'chat.html', {'messages': messages})


@login_required
def send_message(request):
    if request.method == 'POST':
        user = request.user
        content = request.POST.get('content', None)

        if content:
            message = Message.objects.create(user=user, content=content)
            data = {'username': user.username, 'content': content, 'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            return HttpResponse(json.dumps(data), content_type='application/json')

    return HttpResponse(json.dumps({'error': 'Invalid request'}), content_type='application/json')


# Create your views here.
"""
def room(request, user):
    username = request.GET.get('username')
    room_details = Utilisateur.objects.get(username=user)
    return render(request, 'room.html', {'username': username, 'room': user, 'room_details': room_details})


def checkview(request):
    room = request.POST['password']
    username = request.POST['username']

    if Utilisateur.objects.filter(password=room, username=username).exists():
        return redirect('/'+ room + '/?username=' + username)
    else:
        return render(request, "login.html")


def send(request):
    message = request.POST['message']
    username = request.POST['username']
    room_id = request.POST['room_id']

    new_message = Messa.objects.create(value=message, user=username, room=room_id)
    new_message.save()
    return HttpResponse('Message envoyé avec succès')


def getMessages(request, user):
    room_details = Utilisateur.objects.get(username=user)
    messages = Messa.objects.filter(user=room_details.id).order_by('date')
    return JsonResponse({"messages": list(messages.values())})
"""