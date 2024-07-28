from shareplum import Site, Office365
from shareplum.site import Version

import json
import os


USERNAME = "biosafety@blisshealthcare.co.ke"
PASSWORD = "Buma@8349"
SHAREPOINT_URL = "https://blissgvske.sharepoint.com"
SHAREPOINT_SITE = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"


class SharePoint:
    
    def auth(self):
        self.authcookie = Office365(
            SHAREPOINT_URL,
            username=USERNAME,
            password=PASSWORD,
        ).GetCookies()
        self.site = Site(
            SHAREPOINT_SITE,
            version=Version.v365,
            authcookie=self.authcookie,
        )
        return self.site

    def connect_to_list(self, ls_name, columns=None):
        self.auth_site = self.auth()
        list_data = self.auth_site.List(list_name=ls_name).GetListItems()
        
        if columns:
            filtered_list_data = [
                {col: item[col] for col in columns if col in item}
                for item in list_data
            ]
            return filtered_list_data
        else:
            return list_data