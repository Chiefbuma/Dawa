from shareplum import Site, Office365
from shareplum.site import Version

import json
import os


USERNAME = "biosafety@blisshealthcare.co.ke"
PASSWORD = "Streamlit@2024"
SHAREPOINT_URL = "https://blissgvske.sharepoint.com"
SHAREPOINT_SITE = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"


class SharePoint:
    def auth(self):
        try:
            # Authenticate with SharePoint Online (Office 365)
            self.authcookie = Office365(
                SHAREPOINT_URL,
                username=USERNAME,
                password=PASSWORD,
            ).GetCookies()

            # Access the SharePoint site with the obtained cookie
            self.site = Site(
                SHAREPOINT_SITE,
                version=Version.v365,  # Use SharePoint version 365
                authcookie=self.authcookie,
            )
            return self.site

        except Exception as e:
            print(f"Authentication failed: {e}")
            raise

    def connect_to_list(self, ls_name, columns=None):
        try:
            # Authenticate and access the site
            self.auth_site = self.auth()

            # Access the specified list and retrieve list items
            list_data = self.auth_site.List(list_name=ls_name).GetListItems()

            # Filter list data based on provided columns, if any
            if columns:
                filtered_list_data = [
                    {col: item[col] for col in columns if col in item}
                    for item in list_data
                ]
                return filtered_list_data
            else:
                return list_data

        except Exception as e:
            print(f"Failed to retrieve list data: {e}")
            raise