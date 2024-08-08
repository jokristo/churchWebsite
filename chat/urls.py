# chat/urls.py
from django.urls import path
from . import views
"""
websocket_urlpatterns = [
    path('ws/chat/', views.ChatConsumer.as_asgi()),
]
"""
# chat/urls.py
from django.urls import path
from .views import get_messages, post_message

urlpatterns = [
    path('get_messages/', get_messages, name='get_messages'),
    path('post_message/', post_message, name='post_message'),
]
