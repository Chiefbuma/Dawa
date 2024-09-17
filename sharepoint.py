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
            # Authenticate with SharePoint Online (Office 365)
            self.authcookie = Office365(
                SHAREPOINT_URL,
                username=USERNAME,
                password=PASSWORD
            ).GetCookies()

            # Access the SharePoint site with the obtained cookie
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
            sp_list = self.auth_site.List(list_name)
            
            # Get first batch of items
            list_items = sp_list.GetListItems(row_limit=row_limit)
            all_items = list_items["data"]
            
            # Continue retrieving items while more items are available
            while list_items["next_url"]:
                list_items = sp_list.GetListItems(next_url=list_items["next_url"])
                all_items.extend(list_items["data"])
            
            return all_items
        except Exception as e:
            print(f"Failed to retrieve list data: {e}")
            raise

# Example usage
sharepoint = SharePoint()

try:
    data = sharepoint.get_list_items_paginated(list_name="Home Delivery", row_limit=500)
    print(data)
except Exception as e:
    print(f"Error fetching data: {e}")
