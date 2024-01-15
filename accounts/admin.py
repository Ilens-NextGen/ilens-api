from django.contrib import admin
from .models import User, BLToken

admin.site.register(User)
admin.site.register(BLToken)