import copy
import os
import re
import time
from typing import List

import bs4
import requests

from WebScrapper import WebScrapper

# Courts will be assigned the following properties
location_template = {
    "name": "Court Name",
    "branch": "provincial/fedral/military/supreme",
    "type": "appeal/superior/general/administrative_tribunals/null (if supreme)",
    "address": {
        "name": "Office 1",
        "address_line_1": "123 Abc Street",
        "address_line_2": "Extra Detail",
        "city": "Toronto",
        "province": "Ontario",
        "postal_code": "A1B2C3",
        "phone_number": "1234567890",
        "fax": "1234567890",
    },
    "hours_of_operations": {
        0: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Monday",
        },
        1: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Tuesday",
        },
        2: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Wednesday",
        },
        3: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Thursday",
        },
        4: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Friday",
        },
        5: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Saturday",
        },
        6: {
            "times": [
                {"start": "8:00", "stop": "12:00"},
                {"start": "13:00", "stop": "16:30"},
            ],
            "day": "Sunday",
        },
    },
}
hearing_template = {
    "title": "Jack v Bill",
    "party_name": "Jack Jill",
    "lawyer": "Bob",
    "epoch_time": "1582192800",
    "court_file_number": "CV-14-00000000-0000",
    "type": "TRIAL",
    "room_number": "ABC123",
}


class ManitobaCourtsScaper(WebScrapper):
    def __init__(self):
        super().__init__()
        self.baseurl = "https://web43.gov.mb.ca"
        self.location_code_regex = r"(?<=LocationCode\=)(\d\d)"

    def scarpCourts(self, day: int, month: int, year: int):
        """
        Day 0 is Sunday, Day 6 is Saturday
        Month 1 is January, Month 12 is December
        """
        try:
            # Check if the month, day are correct
            if not ((0 <= day <= 6) and (1 <= month <= 12)):
                raise ValueError("Day or month have incorrect range")
            # Check paramter types
            if not (
                (type(day) is int) and (type(month) is int) and (type(year) is int)
            ):
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

                            location_hearings = self.getCourtHearings(
                                20, 2, 2020, location_code, session
                            )
                            # TODO: Use Location name and loctation type
                            #       instead of the name
                            # Get the location name from the text and
                            # remove court type
                            # court_tag.text = "Winnipeg-QB"
                            location_name = court_tag.text
                            all_hearings.append({location_name: location_hearings})

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

    def getCourtHearings(
        self,
        day: int,
        month: int,
        year: int,
        location_code: int,
        session=requests.Session(),
    ):
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

                    # Set the environment to winnipeg time and caulculate the epoch time
                    os.environ["TZ"] = "America/Winnipeg"
                    winnipeg_time = time.strptime(combined_time, r"%d-%b-%Y %H:%M")
                    hearing_info["epoch_time"] = time.mktime(winnipeg_time)
                    # Change back to UTC Time
                    os.environ["TZ"] = "UTC"
                    # Sixth column: Hearing Type
                    hearing_info["type"] = table_data[5].text

                    # Add to all the hearings
                    hearings_list.append(hearing_info)

            # Return all the hearings
            return hearings_list

        return None
