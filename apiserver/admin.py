from django.contrib import admin

from .models import (Court, Hearing, Location, OperationalDay, Room,
                     TimeSlot)
# Register your models here.
admin.site.register(Court)
admin.site.register(Hearing)
admin.site.register(Location)
admin.site.register(OperationalDay)
admin.site.register(Room)
admin.site.register(TimeSlot)
