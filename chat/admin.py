from django.contrib import admin

# Register your models here.
from chat.models import Message, Messa

admin.site.register(Message)
admin.site.register(Messa)

#Room