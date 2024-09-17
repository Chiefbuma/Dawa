from shareplum import Site, Office365
from shareplum.site import Version
import requests

USERNAME = "biosafety@blisshealthcare.co.ke"
PASSWORD = "Streamlit@2024"
SHAREPOINT_URL = "https://blissgvske.sharepoint.com"
SHAREPOINT_SITE = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"

class SharePoint:
    def auth(self):
        try:
            self.authcookie = Office365(
                SHAREPOINT_URL,
                username=USERNAME,
                password=PASSWORD
            ).GetCookies()

            self.site = Site(
                SHAREPOINT_SITE,
                version=Version.v365,
                authcookie=self.authcookie
            )
            return self.site

        except Exception as e:
            print(f"Authentication failed: {e}")
            raise

    def get_list_items_paginated(self, list_name, row_limit=100):
        try:
            self.auth_site = self.auth()
            list_url = f"{SHAREPOINT_SITE}/_api/Web/lists/GetByTitle('{list_name}')/items"
            headers = {
                "Accept": "application/json;odata=verbose",
                "Authorization": f"Bearer {self.authcookie['rtFa']}"
            }

            all_items = []
            skip_token = None
            while True:
                params = {
                    "$top": row_limit,
                    "$select": "UHID, Patientname, mobile, Location, Booking status, Booking Date, Booked on, Booked By, DoctorName, Consultation Status, Consultation Date, Dispatched status, Dispatched Date, Dispatched By, Received Date, Received By, Received Status, Dispensed By, Collection status, Collection Date, Transfer To, Transfer Status, Transfer From, Month, Cycle, MVC",  # Adjust columns as needed
                }
                if skip_token:
                    params["$skiptoken"] = skip_token

                response = requests.get(list_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                items = data.get('d', {}).get('results', [])

                all_items.extend(items)

                # Check for pagination
                if 'd' in data and '__next' in data['d']:
                    skip_token = data['d']['__next']
                else:
                    break

            return all_items
        except Exception as e:
            print(f"Failed to retrieve list data: {e}")
            raise


