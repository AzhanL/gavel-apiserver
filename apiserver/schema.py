from datetime import date, datetime, timedelta

import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType

from .lib.webscrape.ManitobaCourtsScraper import ManitobaCourtsScraper
from .models import Court, Hearing, Location, OperationalDay, Room, TimeSlot


class TimeSlotType(DjangoObjectType):
    class Meta:
        model = TimeSlot


class HearingType(DjangoObjectType):
    class Meta:
        model = Hearing


class RoomType(DjangoObjectType):
    class Meta:
        model = Room


class LocationType(DjangoObjectType):
    class Meta:
        model = Location


class OperationalDaysType(DjangoObjectType):
    class Meta:
        model = OperationalDay


class CourtType(DjangoObjectType):
    class Meta:
        model = Court


class UpdateCourtInfo(graphene.Mutation):
    successful = graphene.Boolean()
    status_message = graphene.String()

    def mutate(parent, info):
        message = ""
        # Check authentication
        if not info.context.user.is_authenticated:
            return UpdateCourtInfo(successful=False,
                                   status_message="Please authenticate")

        # Create a new scraper
        mb_scraper = ManitobaCourtsScraper()
        court_info = mb_scraper.getAllCourtInfo()

        # If if the court info could not be retrieved
        if court_info is None:
            return UpdateCourtInfo(
                successful=False,
                status_message="Could not update the court info")

        # Try updating all court info from json file
        try:
            # TODO: Insert all the courts
            for court in court_info['courts']:
                # Create a list of all court locations
                court_locations = []

                # Update the court location info
                for location in court['locations']:

                    # Get the location or create it
                    location_obj, created = Location.objects.get_or_create(
                        name=location['address']['name'],
                        address_line_1=location['address']['address_line_1'],
                        address_line_2=location['address']['address_line_2'],
                        city=location['address']['city'],
                        province=location['address']['province'],
                        postal_code=location['address']['postal_code'],
                        location_type=location['type'],
                        phone_number=location['address']['phone_number'],
                        fax_number=location['address']['fax'],
                    )

                    # Clear the old timings
                    location_obj.operational_days.clear()

                    # Loop through each timeslot
                    for day in location['address']['hours_of_operations']:
                        time_slots = []
                        week_day = day['day']
                        for json_timeslot in day['times']:
                            # Create the timeslot if it has not been created
                            time_slot_obj, created = TimeSlot.objects.get_or_create(
                                open_time=json_timeslot['start'],
                                close_time=json_timeslot['stop'])
                            # Save the timeslot if newly created
                            if created:
                                time_slot_obj.save()
                            # Create a list of time slot objects
                            time_slots.append(time_slot_obj)

                        # First get the days with any of the time slots
                        days = OperationalDay.objects.filter(
                            time_slots__in=time_slots)
                        # Narrow the day with the exact those time slots(can have other slots as well)
                        for time_slot in time_slots:
                            days = days.filter(time_slots__in=[
                                time_slot,
                            ])

                        found_day = None
                        # Loop through days to find the correct day with the the exact amount of time slots
                        for day in list(days):
                            if (day.time_slots.count() == len(time_slots)
                                ) and (day.week_day == week_day):
                                found_day = day
                                break
                        else:  # Otherwise create a new day the timeslots
                            # Create a new day
                            new_operational_day = OperationalDay(
                                week_day=week_day)
                            # Save the new day
                            new_operational_day.save()
                            # Add all the timeslots
                            for time_slot in time_slots:
                                new_operational_day.time_slots.add(time_slot)
                            # Save the new day
                            new_operational_day.save()
                            found_day = new_operational_day

                        # Add the day to the location
                        location_obj.operational_days.add(found_day)

                    # Save the location
                    location_obj.save()
                    # Add the new location to hte court locaiton
                    court_locations.append(location_obj)

                # Retreive the attributes from JSON,
                # and check if they are empty
                court_branch = str(court['branch'][0]).upper() if len(
                    court['branch']) > 0 else "U"
                court_type = str(court['type'][0]).upper() if len(
                    court['type']) > 0 else "G"
                court_specialization = str(
                    court['specialization'][0]).upper() if len(
                        court['specialization']) > 0 else "G"

                # Get the court the databaseor create one
                court_obj, created = Court.objects.get_or_create(
                    name=court['name'],
                    court_branch=court_branch,
                    court_type=court_type,
                    court_specialization=court_specialization)

                # If the court is newly created, save it first
                if created:
                    court_obj.save()

                # Clear the previous location
                court_obj.locations.clear()

                # Re-add all the locations
                for location in court_locations:
                    court_obj.locations.add(location)

                # Save the new court
                court_obj.save()

            return UpdateCourtInfo(successful=True, status_message=message)

        # Catch error during update
        except Exception:
            return UpdateCourtInfo(successful=False,
                                   status_message="Unknown Error Occurred")


class UpdateHearings(graphene.Mutation):
    successful = graphene.Boolean()
    status_message = graphene.String()

    class Arguments:
        last_days = graphene.Int()
        next_days = graphene.Int()

    def mutate(parent, info, last_days=None, next_days=None):
        # Check authentication or authentication format is wrong\
        if not info.context.user.is_authenticated:
            return UpdateHearings(successful=False,
                                  status_message="Please authenticate")

        scraper = ManitobaCourtsScraper()
        # Create todays dates
        back_date = date.today()
        forward_date = date.today()

        # If parameters given then update dates
        if last_days:
            back_date = date.today() - timedelta(days=last_days)
        if next_days:
            forward_date = date.today() + timedelta(days=next_days)

        # Loop through each days hearings
        while back_date <= forward_date:
            hearings = scraper.scrapeAllCourtHearings(back_date.day,
                                                      back_date.month,
                                                      back_date.year)
            back_date = back_date + timedelta(days=1)

            # Divided first into each court
            for location in hearings:
                # Check proper formatting
                if len(location) == 1:
                    # Seperate the name an the hearing
                    location_name: str = ""
                    hearings = {}
                    location_name, hearings = list(location.items())[0]

                    # Check if any hearings took place that day in the court
                    if len(hearings) <= 0:
                        continue

                    # Remove -QB from the ending
                    if "-QB" in location_name:
                        location_name = location_name[:location_name.
                                                      index("-QB")]

                    # Find Court where its taking place
                    court: Court = Court.objects.filter(
                        Q(name__icontains=location_name)).first()

                    # TODO: Add room numbers when available
                    # Insert each hearing
                    hearing: Dict = {}

                    for hearing in hearings:
                        # TODO: Get room

                        title = hearing.get('title', "")
                        court_file_number = hearing.get(
                            'court_file_number', "")
                        party_name = hearing.get('party_name', "")
                        date_time = datetime.fromtimestamp(
                            hearing.get('epoch_time', 0))
                        lawyer = hearing.get('lawyer', "")
                        hearing_type = hearing.get('type', "")
                        # Create and save the object
                        hearing_obj, created = Hearing.objects.get_or_create(
                            title=title,
                            court_file_number=court_file_number,
                            party_name=party_name,
                            date_time=date_time,
                            lawyer=lawyer,
                            hearing_type=hearing_type,
                            court=court)
                        hearing_obj.save()

        return UpdateHearings(successful=True,
                              status_message="Successfully updated hearings")


class Query(graphene.ObjectType):
    timeslots = graphene.List(TimeSlotType)
    hearings = graphene.List(HearingType,
                             file_number=graphene.String(),
                             date_field=graphene.DateTime(),
                             party_name=graphene.String(),
                             title=graphene.String(),
                             skip=graphene.Int(),
                             count=graphene.Int())
    rooms = graphene.List(RoomType)
    locations = graphene.List(LocationType)
    operational_days = graphene.List(OperationalDaysType)
    courts = graphene.List(CourtType,
                           name_search=graphene.String(),
                           city_search=graphene.String(),
                           province_search=graphene.String(),
                           court_id=graphene.Int())

    def resolve_timeslots(parent, info):
        return TimeSlot.objects.all()

    def resolve_hearings(parent,
                         info,
                         file_number=None,
                         date_field=None,
                         party_name=None,
                         title=None,
                         skip=None,
                         count=None):
        # Check if 1 filter is at least given
        if (file_number is
                None) and (date is None) and (party_name is None) and (
                    title is None) and (skip is None) and (count is None):
            return Hearing.objects.order_by('-date_time')[:count]

        all_hearings = Hearing.objects.all()
        # Filter File number
        if file_number:
            all_hearings = all_hearings.filter(
                Q(court_file_number__icontains=file_number))

        # Filter date
        if date_field:
            all_hearings = all_hearings.filter(
                Q(date_time__year=date_field.year)
                & Q(date_time__month=date_field.month)
                & Q(date_time__day=date_field.day))

        # Search party name
        if party_name:
            all_hearings = all_hearings.filter(
                Q(party_name__icontains=party_name))

        # Skips this many results
        if skip and skip >= 0:
            all_hearings = all_hearings[skip:]

        # Limit the return
        if count:
            if count <= 100 and count >= 0:
                all_hearings = all_hearings[:count]
            else:
                all_hearings = all_hearings[:100]
        else:
            all_hearings = all_hearings[:100]

        # Search title
        if title:
            all_hearings = all_hearings.filter(Q(title__icontains=title))

        return all_hearings[:count]

    def resolve_rooms(parent, info):
        return Room.objects.all()

    def resolve_locations(parent, info):
        return Location.objects.all()

    def resolve_operational_days(parent, info):
        return OperationalDay.objects.all()

    def resolve_courts(parent,
                       info,
                       name_search=None,
                       city_search=None,
                       province_search=None,
                       court_id=None):
        # Courts
        all_courts = Court.objects.all()

        # Check if ID is given
        if court_id:
            return Court.object.filter(pk=court_id)

        # Filter name
        if name_search:
            _filter = Q(name__icontains=name_search)
            all_courts = all_courts.filter(_filter)

        # In City
        if city_search:
            _filter = Q(locations__city__icontains=city_search)
            all_courts = all_courts.filter(_filter).distinct()

        # Proince search
        if province_search:
            _filter = Q(locations__province__icontains=province_search)
            all_courts = all_courts.filter(_filter).distinct()

        return all_courts


class Mutation(graphene.ObjectType):
    update_court_info = UpdateCourtInfo.Field()
    update_hearings = UpdateHearings.Field()
