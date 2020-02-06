from ASPNETFormScrapper import ASPNETFormScrapper
import requests
import copy


class WebScrapper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        self.baseurl = ""

    def getPostHeaders(self) -> dict:
        return {
            **self.headers,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }


class OntarioCourtsScraper(WebScrapper):
    def __init__(self):
        super().__init__()
        self.baseurl = "http://www.ontariocourtdates.ca/"
        self.cookies = {}
        self.extraParams = {}

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

        for counter, city_element in enumerate(cities):
            aspnetScrapper.triggerEvent(
                "ctl00$MainContent$ddlCity",
                city_element.attrs["value"],
                "ctl00_MainContent_UpdatePanel2",
            )

            res = aspnetScrapper.submitForm("ctl00_MainContent_UpdatePanel2", debug=True)
            # Create Headers
            post_headers = copy.deepcopy(aspnetScrapper.headers)
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            # Formulate post data
            aspnetScrapper.updateForm()
            post_data = {}
            post_data.update(
                aspnetScrapper.form_params["ctl00_MainContent_UpdatePanel2"]
            )
            post_data.update(aspnetScrapper.hidden_form_params)

            post_data[
                "ctl00$MainContent$smAjaxTimerControl"
            ] = "ctl00$MainContent$UpdatePanel2|ctl00$MainContent$btnSubmit"
            post_data["ctl00$MainContent$btnSubmit"] = "SUBMIT"

            # Create session and request url
            session = requests.Session()
            response = session.post(
                aspnetScrapper.getResourcePath(),
                data=post_data,
                cookies=aspnetScrapper.cookie_jar,
                headers=post_headers,
            )
            session.close()
            print(response.content)


scrapper = OntarioCourtsScraper()
scrapper.scrapCourts()
print("done")
