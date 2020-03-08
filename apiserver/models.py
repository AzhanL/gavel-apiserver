from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.ca.forms import CAPostalCodeField, CAProvinceField

# Create your models here.


class TimeSlot(models.Model):
    open_time = models.TimeField(verbose_name="Opening Time")
    close_time = models.TimeField(verbose_name="Closing Time")

    def __str__(self):
        return f"{self.open_time.isoformat()} - {self.close_time.isoformat()}"


class OperationalHoursPerDay(models.Model):
    DAYS = [
        ("MO", "Monday"),
        ("TU", "Tuesday"),
        ("WE", "Wednesday"),
        ("TH", "Thursday"),
        ("FR", "Friday"),
        ("SA", "Saturday"),
        ("SU", "Sundary"),
    ]
    week_day = models.CharField(
        verbose_name="Day of the Week", max_length=2, choices=DAYS
    )
    time_slots = models.ManyToManyField(TimeSlot)


class Location(models.Model):
    name = models.CharField(
        verbose_name="Court Address Name", max_length=255, blank=True
    )
    address_line_1 = models.CharField(verbose_name="Address Line 1", max_length=255)
    address_line_2 = models.CharField(
        verbose_name="Address Line 2", max_length=255, blank=True
    )
    city = models.CharField(verbose_name="City Name", max_length=255)
    province = CAProvinceField()
    postal_code = CAPostalCodeField()
    phone_number = PhoneNumberField(verbose_name="Phone Number", blank=True)
    fax_number = PhoneNumberField(verbose_name="Fax Number", blank=True)
    operational_days = models.ManyToManyField(OperationalHoursPerDay)


class Court(models.Model):
    name = models.CharField(verbose_name="Court Name", max_length=255)
    COURT_BRANCHES = [
        ("P", "Provincial"),
        ("F", "Federal"),
        ("M", "Military"),
        ("S", "Supreme"),
    ]
    COURT_TYPES = [
        ("A", "Appeal"),
        ("S", "Superior"),
        ("G", "General"),
        ("T", "Administrative Tribunals"),
        ("X", "Tax")
        # Empty if Supreme Branch
    ]
    COURT_SPECIALIZATION = [
        ("Y", "Youth"),
        ("F", "Family"),
        ("S", "Small Claims"),
    ]
    court_branch = models.CharField(
        verbose_name="Court Branch", max_length=1, choices=COURT_BRANCHES
    )
    court_type = models.CharField(
        verbose_name="Court Type", max_length=1, choices=COURT_TYPES, blank=True
    )
    court_specialization = models.CharField(
        "Court Specialization", max_length=1, choices=COURT_SPECIALIZATION, blank=True
    )
    locations = models.ManyToManyField(Location)


class Room(models.Model):
    room_number = models.CharField(verbose_name="Room Number", max_length=255)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)


class Hearing(models.Model):
    title = models.CharField(verbose_name="Title of Hearing", max_length=255)
    party_name = models.CharField(verbose_name="Name of party", max_length=255)
    lawyer = models.CharField(
        verbose_name="Lawyer Representing Party", max_length=255, blank=True
    )
    epoch_time = models.PositiveIntegerField(verbose_name="Epoch Time")
    court_file_number = models.CharField(verbose_name="File Number", max_length=255)
    hearing_type = models.CharField(verbose_name="Hearing Type", max_length=255)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
