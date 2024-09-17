from shareplum import Site, Office365
from shareplum.site import Version
import json

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

    def connect_to_list(self, ls_name, columns=None):
        try:
            self.auth_site = self.auth()
            sp_list = self.auth_site.List(list_name=ls_name)
            list_data = sp_list.GetListItems()
            
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