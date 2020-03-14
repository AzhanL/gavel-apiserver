import graphene
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field_with_choices

from .models import (Court, Hearing, Location, OperationalDay, Room, TimeSlot)
from graphql import GraphQLError

from .lib.webscrape.ManitobaCourtsScraper import ManitobaCourtsScraper


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
        user = info.context.user

        # if user.is_anonymous:
        #     return UpdateCourtInfo(
        #         successful=False,
        #         status_message="Could not update the court info")

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
                        location_type=location['type'])

                    # Clear the old timings
                    location_obj.operational_days.clear()

                    # Loop through each timeslot
                    for day in location['address']['hours_of_operations']:
                        time_slots = []
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
                            if day.time_slots.count() == len(time_slots):
                                found_day = day
                                break
                        else:  # Otherwise create a new day the timeslots
                            # Create a new day
                            new_operational_day = OperationalDay(
                                week_day=day['day'])
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
                court_type = str(
                    court['type'][0]).upper() if len(court['type']) > 0 else "G"
                court_specialization = str(
                    court['specialization'][0]).upper() if len(
                        court['specialization']) > 0 else "G"

                # Get the court the databaseor create one
                court_obj, created = Court.objects.get_or_create(
                    name=court['name'],
                    court_branch=court_branch,
                    court_type=court_specialization,
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


class Query(graphene.ObjectType):
    timeslots = graphene.List(TimeSlotType)
    hearings = graphene.List(HearingType)
    rooms = graphene.List(RoomType)
    locations = graphene.List(LocationType)
    operational_days = graphene.List(OperationalDaysType)
    courts = graphene.List(CourtType)

    def resolve_timeslots(parent, info):
        return TimeSlot.objects.all()

    def resolve_hearings(parent, info):
        return Hearing.objects.all()

    def resolve_rooms(parent, info):
        return Room.objects.all()

    def resolve_locations(parent, info):
        return Location.objects.all()

    def resolve_operational_days(parent, info):
        return OperationalDay.objects.all()

    def resolve_courts(parent, info):
        return Court.objects.all()


class Mutation(graphene.ObjectType):
    update_court_info = UpdateCourtInfo.Field()
