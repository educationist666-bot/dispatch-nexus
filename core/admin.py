from django.contrib import admin
from .models import Company, UserProfile, Driver, Load

admin.site.register(Company)
admin.site.register(UserProfile)
admin.site.register(Driver)
admin.site.register(Load)