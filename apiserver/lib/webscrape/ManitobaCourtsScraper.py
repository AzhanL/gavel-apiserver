import calendar
import copy
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import List

import bs4
import requests

from .WebScraper import WebScraper

# Courts will be assigned the following properties
court_template = {
    "name":
    "Court Name",
    "branch":
    "provincial/federal/military/supreme",
    "type":
    "appeal/superior/general/administrative_tribunals/tax/null (if supreme)",
    "specialization":
    "",
    "locations": [
        {
            "type": "Court Office/Hearing",
            "address": {
                "name": "Office 2",
                "address_line_1": "123 Abc Street",
                "address_line_2": "Extra Detail",
                "city": "Toronto",
                "province": "Ontario",
                "postal_code": "A1B2C3",
                "phone_number": "1234567890",
                "fax": "1234567890",
                "purpose": "For Hearings",
                "hours_of_operations": {
                    0: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Monday",
                    },
                    1: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Tuesday",
                    },
                    2: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Wednesday",
                    },
                    3: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Thursday",
                    },
                    4: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Friday",
                    },
                    5: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Saturday",
                    },
                    6: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Sunday",
                    },
                },
            },
        },
        {
            "type": "Court Office/Hearing",
            "address": {
                "name": "Office 2",
                "address_line_1": "123 Abc Street",
                "address_line_2": "Extra Detail",
                "city": "Toronto",
                "province": "Ontario",
                "postal_code": "A1B2C3",
                "phone_number": "1234567890",
                "fax": "1234567890",
                "purpose": "For Hearings",
                "hours_of_operations": {
                    0: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Monday",
                    },
                    1: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Tuesday",
                    },
                    2: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Wednesday",
                    },
                    3: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Thursday",
                    },
                    4: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Friday",
                    },
                    5: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Saturday",
                    },
                    6: {
                        "times": [
                            {
                                "start": "8:00",
                                "stop": "12:00"
                            },
                            {
                                "start": "13:00",
                                "stop": "16:30"
                            },
                        ],
                        "day":
                        "Sunday",
                    },
                },
            },
        },
    ],
}
hearing_template = {
    "title": "",
    "party_name": "",
    "lawyer": "",
    "epoch_time": "",
    "court_file_number": "",
    "type": "",
    "room_number": "",
}
hearing_template_sample = {
    "title": "Jack v Bill",
    "party_name": "Jack Jill",
    "lawyer": "Bob",
    "epoch_time": "1582192800",
    "court_file_number": "CV-14-00000000-0000",
    "type": "TRIAL",
    "room_number": "ABC123",
}


class ManitobaCourtsScraper(WebScraper):
    def __init__(self):
        super().__init__()
        self.baseurl = "https://web43.gov.mb.ca"
        self.location_code_regex = r"(?<=LocationCode\=)(\d\d)"

    def scrapeAllCourtHearings(self, day: int, month: int, year: int):
        """
        Day is day of the month
        Month 1 is January, Month 12 is December

        Scrapes court hearings from all court locations available on the site
        """
        try:
            # Check if the month, day are correct
            if not ((0 <= day <= 31) and (1 <= month <= 12)):
                raise ValueError("Day or month have incorrect range")
            # Check paramter types
            if not ((type(day) is int) and (type(month) is int) and
                    (type(year) is int)):
                raise TypeError("Day, month or year are incorrect type")

            # Create a new request session
            session = requests.Session()
            # Create the url to retrieve the locations on the main page
            url = self.baseurl + "/Registry/DailyCourtHearing"
            response = session.get(url, headers=self.headers)
            # Check if the status code is 200
            if response.status_code == 200:
                # Parse the whole page
                soup = bs4.BeautifulSoup(response.content.decode(), "lxml")
                # Get the a tags which include the name of the courts
                court_tags = soup.select(".tableCenter > tr > td > a")
                # Prepare return value
                all_hearings: List = []
                # Run through each court
                for court_tag in court_tags:
                    # Extract the href attribute
                    href = court_tag.attrs["href"] or None
                    if href:
                        # Try to find the location code from
                        # within the href attribute
                        matches = re.search(self.location_code_regex, href)
                        # If there is one
                        if matches:
                            # Location is code is group 0 of the regex
                            location_code = matches.group(0)

                            location_hearings = self.scrapeCourtHearings(
                                day, month, year, location_code, session)
                            # TODO: Use Location name and loctation type
                            #       instead of the name
                            # Get the location name from the text and
                            # remove court type
                            # court_tag.text = "Winnipeg-QB"
                            location_name = court_tag.text
                            all_hearings.append(
                                {location_name: location_hearings})

                # Return all the hearing retrieved
                return all_hearings

            else:
                raise Exception("Invalid response")
        except ValueError:
            return None
        except TypeError:
            return None
        except Exception:
            return None

    def scrapeCourtHearings(
        self,
        day: int,
        month: int,
        year: int,
        location_code: int,
        session=requests.Session(),
    ):
        """
        Scrapes court hearings from 1 court court location
        """
        # Prepare paramters to be sent
        params = {
            "HearingTypeCode": "all",
            "LocationCode": str(location_code),
            "SortOrder": "H",
            "Day": str(day),
            "Month": str(month),
            "Year": str(year),
            "X-Requested-With": "XMLHttpRequest",
        }
        # Create the url
        url = self.baseurl + "/Registry/DailyCourtHearing/SearchResults"
        # Request the page with the parameters
        response = session.get(url, headers=self.headers, params=params)

        # Check if the response is valid
        if response.status_code == 200:
            # Create a beautiful soup object
            soup = bs4.BeautifulSoup(response.content.decode(), "lxml")
            # Extract the table row (which are the hearing entries) from the soup object
            table_rows = soup.body.table.tbody.find_all("tr")
            hearings_list: List = []
            # For each row, extract the data
            for tr in table_rows:
                # Make a template for the data
                hearing_info = copy.deepcopy(hearing_template)
                # Extract the columns
                table_data = list(filter(lambda td: td != "\n", tr.contents))

                # Check if it has the correct number of columns
                if len(table_data) == 6:
                    # First column: Party Name
                    hearing_info["party_name"] = table_data[0].text
                    # Second column: Lawyer
                    hearing_info["lawyer"] = table_data[1].text
                    # Third column: Court File Number
                    hearing_info["court_file_number"] = table_data[2].text
                    # Fifth column: Court date-time
                    combined_time = f"{table_data[3].text} {table_data[4].text}"

                    # Create a time format to parse time
                    time_format = r"%d-%b-%Y %H:%M"
                    # caulculate the epoch time
                    winnipeg_time = datetime.strptime(combined_time,
                                                      time_format)

                    # UTC Offset
                    hearing_info[
                        'utc_offset'] = " -0500" if self.isDaylightSavingTime(
                            winnipeg_time) else " -0600"

                    # Add the timezone
                    combined_time += hearing_info['utc_offset']
                    # Create new time format with timezone
                    time_format = r"%d-%b-%Y %H:%M %z"

                    # Create a new time
                    winnipeg_time = datetime.strptime(combined_time,
                                                      time_format)
                    # Set the epoch time
                    hearing_info["epoch_time"] = winnipeg_time.timestamp()
                    # Sixth column: Hearing Type
                    hearing_info["type"] = table_data[5].text

                    # Add to all the hearings
                    hearings_list.append(hearing_info)

            # Return all the hearings
            return hearings_list

        return None

    def getAllCourtInfo(self):
        try:
            # Try reading the json file and return it
            json_file = open("apiserver/static/manitoba_courts.json", "r")
            if json_file.closed is False:
                json_data = json.loads(json_file.read())
                return json_data

            return None
        except OSError:
            # Could not open the file
            return None
        except Exception:
            # Unknown error occurred
            return None
        return None

    def isDaylightSavingTime(self, datetime_obj: datetime):
        # Daylight saving act refer to: https://web2.gov.mb.ca/laws/statutes/ccsm/o030e.php
        # 2006 has special day light saving time for 2006
        if datetime_obj.year == 2006:
            # Get the start of DST (first sunday of april, 02:00)
            start_dst = self.forwardDayOfMonth(calendar.SUNDAY, 2016, 4, 2, 0,
                                               0, 1)
            # Get the end of DST (last sunday of october, 02:00)
            end_dst = self.backwardDayOfMonth(calendar.SUNDAY, 2016, 10, 2, 0,
                                              0, 1)

            return start_dst <= datetime_obj <= end_dst
        # 2017 and onward
        elif datetime_obj.year >= 2007:
            # Get the start of DST (second sunday of march, 02:00)
            start_dst = self.forwardDayOfMonth(calendar.SUNDAY,
                                               datetime_obj.year, 3, 2, 0, 0,
                                               2)
            # Get the end of DST (first sunday of november, 02:00)
            end_dst = self.forwardDayOfMonth(calendar.SUNDAY,
                                             datetime_obj.year, 11, 2, 0, 0, 1)

            return start_dst <= datetime_obj <= end_dst

        # Previous years did not have DST
        elif datetime_obj.year <= 2005:
            return false

    def forwardDayOfMonth(self,
                          day_of_week,
                          year,
                          month,
                          hour,
                          minute,
                          second,
                          position=1) -> datetime:
        try:
            # Position 1 means first day of month, 2 means second day of month
            start_day, days_in_month = calendar.monthrange(year, month)
            offset = (day_of_week - start_day) % 7
            first_of_month = datetime(year,
                                      month,
                                      1,
                                      hour=hour,
                                      minute=minute,
                                      second=second)

            first_day_of_month = first_of_month + timedelta(days=(offset + (
                (position - 1) * 7)))
            return first_day_of_month

        except Exception:
            return None

    def backwardDayOfMonth(self,
                           day_of_week,
                           year,
                           month,
                           hour,
                           minute,
                           second,
                           position=1) -> datetime:
        try:
            # Position 1 means last day of month, position 2 means second last day of month
            start_day, days_in_month = calendar.monthrange(year, 4)
            offset = (day_of_week -
                      calendar.weekday(year, month, days_in_month)) % 7
            last_of_month = datetime(year,
                                     month,
                                     days_in_month,
                                     hour=hour,
                                     minute=minute,
                                     second=second)

            last_day_of_month = last_of_month - timedelta(days=(offset + (
                (position - 1) * 7)))
            return last_day_of_month

        except Exception:
            return None
