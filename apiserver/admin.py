from django.contrib import admin

from .models import (Court, Hearing, Location, OperationalDay, Room, TimeSlot)


# Register your models here.
@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    pass


@admin.register(Hearing)
class HearingAdmin(admin.ModelAdmin):
    list_display = [
        'court_file_number', 'title', 'party_name', 'lawyer', 'date_time',
        'hearing_type', 'court'
    ]
    search_fields = [
        'title__icontains',
        'court_file_number__icontains',
        'party_name__icontains',
        'lawyer__icontains',
    ]
    list_filter = ('hearing_type', 'court')
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
