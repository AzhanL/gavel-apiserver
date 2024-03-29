from ASPNETFormScrapper import ASPNETFormScrapper
import requests
import copy
import sys
from .WebScraper import WebScraper


class OntarioCourtsScraper(WebScraper):
    def __init__(self):
        super().__init__()
        self.baseurl = "http://www.ontariocourtdates.ca/"
        self.cookies = {}
        self.extraParams = {}
        self.tries_before_quit = 2

    def scrapCourts(self):
        aspnetScrapper = ASPNETFormScrapper("http://www.ontariocourtdates.ca/")
        aspnetScrapper.visit(
            site_url="http://www.ontariocourtdates.ca/", form_id="aspnetForm"
        )
        aspnetScrapper.triggerEvent("ctl00$MainContent$chkAgree", "on")
        aspnetScrapper.submitForm()

        aspnetScrapper.setUpdatePanel()
        court_types = aspnetScrapper.aspnet_form.find(
            id="ctl00_MainContent_ddlCourt"
        ).find_all("option")[1:]
        cities = aspnetScrapper.aspnet_form.find(
            id="ctl00_MainContent_ddlCity"
        ).find_all("option")[1:]
        sys.setrecursionlimit(10000)

        cities_with_error = []
        while len(cities) != 0:
            for counter, city_element in enumerate(cities):
                res = ""
                next = False
                tries = 0
                while next is False:
                    try:
                        temp_scrapper = copy.deepcopy(aspnetScrapper)
                        
                        city_name = city_element.attrs["value"]
                        temp_scrapper.triggerEvent(
                            "ctl00$MainContent$ddlCity",
                            city_name,
                            "ctl00_MainContent_UpdatePanel2",
                        )

                        res = temp_scrapper.submitForm("ctl00_MainContent_UpdatePanel2", debug=True)
                        status_code = res.decode().split('|')[0]
                        # Check if the response is 69 code indication its a dataitem
                        if status_code == '69':
                            next = True
                            cities.pop(counter)
                            break

                        if not next:
                            print(f"Trying to get URL for {city_name} again")
                            tries += 1
                    except:
                        next = False
                        tries += 1

                    if tries > self.tries_before_quit and next is False:
                        print(f"Quit trying to get update for {city_name}")
                        break
                
                if next:
                    print(res)


scrapper = OntarioCourtsScraper()
scrapper.scrapCourts()
print("done")
