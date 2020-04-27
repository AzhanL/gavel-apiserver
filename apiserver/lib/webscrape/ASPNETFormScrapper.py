import requests
import bs4
import logging
import datetime
import copy
import re
import json

from typing import List, Dict


class ASPNETFormScrapper:
    def __init__(
        self,
        url="http://localhost",
        form_id: str = "",
        update_panels_available: bool = False,
    ):
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
        self.url = url
        self.update_panels_available = update_panels_available
        self.page_content: bytes = None
        self.aspnet_form: bs4.BeautifulSoup = None
        self.form_action = ""
        self.form_id = form_id
        self.form_params = {}
        self.hidden_form_params = {}
        self.html_form_elements = ["input", "select", "button"]
        self.cookie_jar: requests.sessions.RequestsCookieJar = requests.sessions.RequestsCookieJar()
        self.update_panels_available: bool = False
        # Panel Name Regex
        self.panel_name_regex = r"(?<=\')(tctl)((\w|\$)*)((\w|\$)*)(?=\')"
        # Time Controllers Regex
        self.timer_contollers_regex = r"(?<=_initialize\(\')(\w|\$)*(?=\')"
        # Store all the update panels and time variables to empty
        self.aspnet_update_panels: List[bs4.BeautifulSoup] = []
        self.panel_content: Dict[str:str] = {}
        self.aspnet_timers: List[str] = []

    def visit(
        self,
        site_url: str = "",
        request_type: str = "GET",
        request_data: dict = None,
        form_id: str = None,
    ) -> requests.Response:
        # Create a session and set default headers
        session = requests.Session()
        session.headers.update(self.headers)

        # GET/POST Data
        response = None
        if request_type == "GET":
            response = session.get(site_url, timeout=10)
        elif request_type == "POST":
            response = session.post(site_url, data=request_data, timeout=10)

        # If there is a reponse then the hidden
        # input are autoupdated for next request
        if response is not None:
            if response.status_code == 200:
                # Update page content and return response
                self.page_content = response.content
                self.updateForm(form_id)

        return response

    def updateForm(self, form_id: str = None) -> bs4.BeautifulSoup:
        # Create a beautifulsoup object
        soup = bs4.BeautifulSoup(self.page_content, "lxml")
        # Find the first form or a form by its ID
        try:
            aspnetForm = (
                soup.find("form")
                if form_id is None
                else list(soup.select(f"#{form_id}"))[0]
            )
        except IndexError:
            print("Index Error(line 115-119) occured while trying to set the form ")
        # update the form
        try:
            self.form_action = aspnetForm.attrs["action"]
            self.form_id = aspnetForm.attrs["id"]
            self.aspnet_form = aspnetForm
            # Update form fields
            self.updateFormFields(filter_submit=True)
            # Return form
            return aspnetForm
        except:
            print("Error updating form(line 124)")

        return False

    def updateFormFields(self, filter_attrs={}, filter_type="any", filter_submit=False):
        fields = []
        self.form_params = {}
        # Filter the submit field; needed when triggering an event
        # instead of submitting the page
        filter_copy = copy.deepcopy(filter_attrs)
        if filter_submit is True:
            filter_copy["type"] = "submit"

        # TODO: Update to comply with different update panels
        if self.update_panels_available is False:
            # Get all the fields
            for form_tag in self.html_form_elements:
                # Appending the list not adding a list inside a list
                fields += [field for field in self.aspnet_form.find_all(form_tag)]

            # Filter fields
            fields = ASPNETFormScrapper.filter_field_list(
                fields, filter_copy, filter_type
            )

            self.form_params["default"] = {
                field.attrs["name"]: ASPNETFormScrapper.getAttributeValue(field)
                for field in fields
                if "name" in field.attrs.keys()
            }
            # Update hidden fields
            self.updateHiddenFields(filter_copy, filter_type)
            # Returns list of beautifulsoup fileds
            return True

        elif self.update_panels_available is True:
            # Identify the update panels
            self._identify_aspnet_panel_and_timer()

            # Get all the fields within each panel
            for panel in self.aspnet_update_panels:
                fields = []
                for form_tag in self.html_form_elements:
                    # Appending the list not adding a list inside a list
                    fields += [field for field in panel.find_all(form_tag)]

                # Filter fields for the panels
                fields = ASPNETFormScrapper.filter_field_list(
                    fields, filter_copy, filter_type
                )

                self.form_params[panel.attrs["id"]] = {
                    field.attrs["name"]: ASPNETFormScrapper.getAttributeValue(field)
                    for field in fields
                    if "name" in field.attrs.keys()
                }
            # Update hidden fields
            self.updateHiddenFields(filter_copy, filter_type)

            return True

        return False

    def updateHiddenFields(self, filter_attrs={}, filter_type="any"):
        fields = []
        # Get all the fields
        fields += [field for field in self.aspnet_form.find_all_next(type="hidden")]
        # Filter fields
        fields = [
            field
            for field in fields
            if ASPNETFormScrapper.pass_attr_filter(
                field.attrs, filter_attrs, filter_type
            )
        ]
        # Hidden params for the default update panel
        self.hidden_form_params = {
            field.attrs["name"]: ASPNETFormScrapper.getAttributeValue(field)
            for field in fields
            if "name" in field.attrs.keys()
        }

        # Returns list of beautifulsoup fileds
        return fields

    def updateFormFromPanelUpdate(self, update_content: bytes):
        content = update_content.decode()
        content_sections: List[str] = list(content.split("|"))
        try:
            # Update Panel Content
            updated_panel_name = content_sections[
                content_sections.index("updatePanel") + 1
            ]
            updated_panel_content = content_sections[
                content_sections.index("updatePanel") + 2
            ]
            self.panel_content[updated_panel_name] = updated_panel_content

            # Update the panels contents
            current_update_panel_names = [
                str(panel.attrs["id"]) for panel in self.aspnet_update_panels
            ]
            updated_panel_location = current_update_panel_names.index(
                updated_panel_name
            )
            # Clear and update with new panel content
            self.aspnet_update_panels[updated_panel_location].div.clear()
            self.aspnet_update_panels[updated_panel_location].div.append(
                bs4.BeautifulSoup(updated_panel_content)
            )
            self.aspnet_form.find(id=updated_panel_name).div.clear()
            self.aspnet_form.find(id=updated_panel_name).div.append(
                bs4.BeautifulSoup(updated_panel_content)
            )

            # Update hidden params
            hidden_field_locations = [
                counter
                for counter, item in enumerate(content_sections)
                if item == "hiddenField"
            ]
            for location in hidden_field_locations:
                hidden_field_id = content_sections[location + 1]
                hidden_field_value = content_sections[location + 2]
                self.hidden_form_params[hidden_field_id] = hidden_field_value
                self.aspnet_form.find(id=hidden_field_id).attrs['value'] = hidden_field_value

        except ValueError:
            print(
                "Could not update the panel because updatePanel string is not found in update_content"
            )
            return False

    @staticmethod
    def pass_attr_filter(
        tag_attrs: dict = {"tag": "value"},
        filter_attrs: dict = {"type": "hidden"},
        filter_type="any",
    ):
        # When there are no filters present, then it automatically passes
        if len(filter_attrs.keys()) == 0:
            return True
        # Tags that both the tag and the filter has
        tags_in_common = set(tag_attrs.keys()).intersection(set(filter_attrs.keys()))
        # Matches will be used to count the amount of filters matched
        matches = {}
        for tag in tags_in_common:
            if tag_attrs[tag] == filter_attrs[tag]:
                # If any filter triggered
                if filter_type == "any":
                    return False
                # All filters must be triggered it to fail
                elif filter_type == "all":
                    matches[tag] = filter_type[tag]

        # If all the filters have been triggered
        if filter_type == "all" and len(matches.keys()) == len(filter_attrs.keys()):
            return False
        # Filter passes otherwise
        return True

    @staticmethod
    def filter_field_list(
        fields: List[bs4.BeautifulSoup], filter_attrs: dict, filter_type: str
    ):
        return [
            field
            for field in fields
            if ASPNETFormScrapper.pass_attr_filter(
                field.attrs, filter_attrs, filter_type
            )
        ]

    @staticmethod
    def getAttributeValue(beautifulsoup_element: bs4.BeautifulSoup = None):
        # Check if a beautiful soup element has been supplied
        if beautifulsoup_element is not None:
            # Extract its attributes
            element_attributes = beautifulsoup_element.attrs
            # Get its type otherwise set it to none
            element_type = element_attributes.get("type", None)

            # If it has type a then determine its value
            if (
                beautifulsoup_element.name == "input"
                and element_type is not None
                and type(element_type) == str
            ):
                element_value = ""
                # From the type determine its value
                if element_type == "checkbox":
                    element_value = (
                        "on"
                        if element_attributes.get("checked", "unchecked") == "checked"
                        else ""
                    )
                elif element_type in ["hidden", "submit"]:
                    element_value = element_attributes.get("value", "")

                # Return element value
                return element_value
            elif beautifulsoup_element.name == "select":
                selected = beautifulsoup_element.find_next(
                    attrs={"selected": "selected"}
                )
                if selected is None:
                    selected = beautifulsoup_element.find_next('option')
                return selected.attrs["value"] if selected is not None else None

    def getResourcePath(self, resource: str = None) -> str:
        # Path is form action by defaul or to the resource specified
        res_path = (
            self.url + self.form_action if resource is None else self.url + resource
        )
        return res_path

    def triggerEvent(
        self,
        event_name="name",
        event_value="value",
        panel_id: str = None,
        extra_post_data={},
    ):
        # When there are no panels
        if self.update_panels_available is False:
            # Update params without submit button
            self.updateFormFields(filter_submit=True)

            # Formulate new parameters for the trigger event
            new_params: dict = {}
            new_params["__EVENTTARGET"] = event_name
            new_params[event_name] = event_value

            # Formulate post paramters from previous state
            # and update with the new paramters
            post_data: dict = {}
            post_data.update(self.form_params["default"])
            post_data.update(new_params)
            post_data.update(extra_post_data)

            post_headers = copy.deepcopy(self.headers)
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"

            # Create a new session
            session = requests.Session()
            response = session.post(
                self.getResourcePath(),
                headers=post_headers,
                data=post_data,
                cookies=self.cookie_jar,
            )
            self.cookie_jar.update(session.cookies)
            session.close()

            # Update page content and form
            self.page_content = response.content
            print(
                response.content.decode(),
                file=open("regulartrigger_response_content.aspx", "w"),
            )
            self.updateForm(self.form_id)

            return response.content

        # If there are update panels available
        elif (
            self.update_panels_available is True
            and panel_id is not None
            and panel_id in [panel.attrs["id"] for panel in self.aspnet_update_panels]
        ):
            # Update params without submit button
            self.updateFormFields(filter_submit=True)

            # Formulate new parameters for the trigger event
            new_params: dict = {}
            new_params["__EVENTTARGET"] = event_name
            new_params[event_name] = event_value

            # Add the ajax timer
            new_params[
                self.aspnet_timers[0]
            ] = f"{panel_id.replace('_', '$')}|{event_name}"

            # Formulate post paramters from previous state
            # and update with the new paramters
            post_data: dict = {}
            post_data.update(self.form_params[panel_id])
            post_data.update(self.hidden_form_params)
            post_data.update(new_params)
            post_data.update({"__ASYNCPOST": "true"})
            post_data.update(extra_post_data)

            post_headers = copy.deepcopy(self.headers)
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            if self.aspnet_update_panels is True:
                post_headers.update({"X-MicrosoftAjax": "Delta=true"})

            # Create a new session
            session = requests.Session()
            response = session.post(
                self.getResourcePath(),
                headers=post_headers,
                data=post_data,
                cookies=self.cookie_jar,
            )
            self.cookie_jar.update(session.cookies)
            session.close()
            print(
                response.content.decode(),
                file=open("paneltrigger_response_content.aspx", "w"),
            )

            # Update page content and form
            self.updateFormFromPanelUpdate(response.content)
            self.page_content = self.aspnet_form.prettify().encode("utf-8")
            self.updateForm(self.form_id)

            return response.content

        return False

    def submitForm(self, panel_id: str = "default", extra_post_data={}, debug=False):
        # Update form with submit button
        self.updateFormFields()
        # Formulate post paramters from previous state
        # and update with the new paramters
        post_data: dict = {}
        if self.update_panels_available is False:
            post_data.update(self.form_params["default"])
        elif self.update_panels_available is True:
            post_data.update(self.form_params[panel_id])
            submit_btn = self.aspnet_form.find(id=panel_id).find(
                attrs={"type": "submit"}
            )
            post_data[
                self.aspnet_timers[0]
            ] = f"{panel_id.replace('_', '$')}|{submit_btn.attrs['name']}"
            post_data.update({"__ASYNCPOST": "true"})

        post_data.update(self.hidden_form_params)
        post_data.update(extra_post_data)

        # Formulate post header
        post_headers = copy.deepcopy(self.headers)
        post_headers[
            "Content-Type"
        ] = "application/x-www-form-urlencoded; charset=utf-8"

        if self.update_panels_available is True:
            post_headers.update({"X-MicrosoftAjax": "Delta=true"})

        print(json.dumps(post_data), file=open("post_data.json", "w"))
        print(json.dumps(post_headers), file=open("post_headers.json", "w"))
        # Create a new session
        session = requests.Session()
        
        response = session.post(
            self.getResourcePath(),
            headers=post_headers,
            data=post_data,
            cookies=self.cookie_jar,
        )

        # Extract the cookie if there are any
        self.cookie_jar.update(session.cookies)
        # Close the session
        session.close()
        # Update the content
        self.page_content = response.content
        # if self.update_panels_available:
        #     if response.content.decode().split('|')[1] == 'updatePanel':
        #         self.updateFormFromPanelUpdate(response.content)
        #         return self.submitForm(panel_id, extra_post_data, debug)

        return response.content

    def setUpdatePanel(
        self,
        update_panels_available: bool = True,
        formID: str = "aspnetForm",
        ajax_control_timer: str = "ctl00$MainContent$smAjaxTimerControl",
    ):
        self.update_panels_available = update_panels_available
        self.updateForm()
        return True

    def _identify_aspnet_panel_and_timer(self):
        # TODO: This conflicts with updateForm; which comes first or should
        # Finds the names of the timers and update panels
        ajax_timer_names = [
            match.group()
            for match in re.finditer(
                self.timer_contollers_regex, self.page_content.decode(), re.MULTILINE
            )
        ]
        panel_names = [
            match.group()[1:]
            for match in re.finditer(
                self.panel_name_regex, self.page_content.decode(), re.MULTILINE
            )
        ]

        # If there is both timers and update panels then set panels avaialble to true
        if len(ajax_timer_names) > 0 and len(panel_names) > 0:
            panels_available = True

        # Set the class aspnet timers to their names
        self.aspnet_timers = ajax_timer_names
        # Set the class update panels
        self.aspnet_update_panels = [
            self.aspnet_form.select(f"#{str(panel_name).replace(r'$', r'_')}")[0]
            for panel_name in panel_names
        ]

        return True

