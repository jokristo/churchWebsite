from datetime import datetime

from django.db import models
# from datetime import datetime

# Create your models here.

from compte.models import Utilisateur

Utilisateur


class Message(models.Model):
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, default=1)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.timestamp}'


class Messa(models.Model):
    value = models.CharField(max_length=1000000)
    date = models.DateTimeField(default=datetime.now, blank=True)
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
