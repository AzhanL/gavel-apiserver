from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.ca.ca_provinces import PROVINCE_CHOICES

# Create your models here.


class TimeSlot(models.Model):
    open_time = models.TimeField(verbose_name="Opening Time")
    close_time = models.TimeField(verbose_name="Closing Time")

    def __str__(self):
        return f"{self.open_time} - {self.close_time}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['open_time', 'close_time'],
                                    name="unique_timeslot"),
        ]


class OperationalDay(models.Model):
    DAYS = [
        ("MO", "Monday"),
        ("TU", "Tuesday"),
        ("WE", "Wednesday"),
        ("TH", "Thursday"),
        ("FR", "Friday"),
        ("SA", "Saturday"),
        ("SU", "Sundary"),
    ]
    week_day = models.CharField(verbose_name="Day of the Week",
                                max_length=2,
                                choices=DAYS)
    time_slots = models.ManyToManyField(TimeSlot)

    def __str__(self):
        return f"{self.week_day} - {self.id}"


class Location(models.Model):
    name = models.CharField(verbose_name="Court Address Name",
                            max_length=255,
                            blank=True)
    address_line_1 = models.CharField(verbose_name="Address Line 1",
                                      max_length=255)
    address_line_2 = models.CharField(verbose_name="Address Line 2",
                                      max_length=255,
                                      blank=True)
    city = models.CharField(verbose_name="City Name", max_length=255)
    province = models.CharField(verbose_name="Province",
                                max_length=2,
                                choices=PROVINCE_CHOICES,
                                blank=False,
                                default="ON")
    postal_code = models.CharField(verbose_name="Postal Code",
                                   max_length=6,
                                   blank=False,
                                   null=True)
    phone_number = PhoneNumberField(verbose_name="Phone Number", blank=True)
    fax_number = PhoneNumberField(verbose_name="Fax Number", blank=True)
    operational_days = models.ManyToManyField(OperationalDay)
    location_type = models.CharField(verbose_name="Location Type",
                                     max_length=255,
                                     blank=True)

    def __str__(self):
        output_name = (self.name + ' - ') if (self.name != '') else ("")
        return f"{output_name}{self.city}, {self.province}, {self.postal_code}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=[
                'name', 'address_line_1', 'address_line_2', 'city', 'province',
                'postal_code', 'location_type', 'phone_number', 'fax_number'
            ],
                                    name="unique_location")
        ]


class Court(models.Model):
    name = models.CharField(verbose_name="Court Name", max_length=255)
    COURT_BRANCHES = (("P", "Provincial"), ("F", "Federal"), ("M", "Military"),
                      ("S", "Supreme"), ("U", "Unknown"))
    # Empty if Supreme Branch
    COURT_TYPES = (("A", "Appeal"), ("S", "Superior"), ("G", "General"),
                   ("T", "Administrative Tribunals"), ("X", "Tax"))
    COURT_SPECIALIZATION = (("Y", "Youth"), ("F", "Family"),
                            ("S", "Small Claims"), ("G", "General"))
    court_branch = models.CharField(verbose_name="Court Branch",
                                    max_length=1,
                                    choices=COURT_BRANCHES,
                                    default="U")
    court_type = models.CharField(verbose_name="Court Type",
                                  max_length=1,
                                  choices=COURT_TYPES,
                                  default="G")
    court_specialization = models.CharField("Court Specialization",
                                            max_length=1,
                                            choices=COURT_SPECIALIZATION,
                                            default="G")
    locations = models.ManyToManyField(Location)

    def __str__(self):
        province = self.locations.first().province
        return f"{self.name} ({province})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=[
                'name', 'court_branch', 'court_type', 'court_specialization'
            ],
                                    name="unique_court")
        ]


class Room(models.Model):
    room_number = models.CharField(verbose_name="Room Number", max_length=255)
    location = models.ForeignKey(Location,
                                 on_delete=models.SET_NULL,
                                 null=True)

    def __str__(self):
        location_name = self.location if (self.location is not None) else ""
        return f"{location_name} - Room:{self.room_number}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['room_number', 'location'],
                                    name="unique_room")
        ]


class Hearing(models.Model):
    title = models.CharField(verbose_name="Title of Hearing", max_length=255)
    party_name = models.CharField(verbose_name="Name of party", max_length=255)
    lawyer = models.CharField(verbose_name="Lawyer Representing Party",
                              max_length=255,
                              blank=True)
    date_time = models.DateTimeField(verbose_name="Date & Time",
                                     blank=True,
                                     null=True)
    court_file_number = models.CharField(verbose_name="File Number",
                                         max_length=255)
    hearing_type = models.CharField(verbose_name="Hearing Type",
                                    max_length=255)
    room = models.ForeignKey(Room,
                             on_delete=models.SET_NULL,
                             null=True,
                             blank=True)

    def __str__(self):
        title = self.title + " - " if (self.title is not None) or (
            self.title != "") else ""
        file_num = self.court_file_number + " - " if (
            self.court_file_number is not None) or (
                self.court_file_number != "") else ""
        party_name = self.party_name + " - " if (
            self.party_name is not None) or (self.party_name != "") else ""
        date_time = self.date_time.strftime(
            "%b %d, %Y (%H:%M)") if self.date_time is not None else ""
        return f"{file_num}{title}{party_name}{date_time}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=[
                'date_time', 'court_file_number', 'party_name', 'hearing_type',
                'lawyer'
            ],
                                    name="unique_hearing")
        ]
