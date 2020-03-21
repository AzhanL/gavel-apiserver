from django.contrib import admin

from .models import (Court, Hearing, Location, OperationalDay, Room, TimeSlot)


# Register your models here.
@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    pass


@admin.register(Hearing)
class HearingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'party_name', 'lawyer', 'date_time', 'court_file_number',
        'hearing_type', 'court'
    ]
    search_fields = ['court_file_number']
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(OperationalDay)
class OperationalDay(admin.ModelAdmin):
    pass


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    pass
