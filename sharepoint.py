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
    
    def connect_to_list(self, ls_name, columns=None, query=None, next_page=None):
        try:
            self.auth_site = self.auth()
            sp_list = self.auth_site.List(list_name=ls_name)
            
            # Fetch list data, handle next_page for pagination if applicable
            if next_page:
                list_data = sp_list.GetListItems(query=query, next_page=next_page)
            else:
                list_data = sp_list.GetListItems(query=query)
            
            # If the list_data is a list, process it directly
            if isinstance(list_data, list):
                # Process list data
                if columns:
                    filtered_list_data = [
                        {col: item.get(col, None) for col in columns}
                        for item in list_data  # Directly iterate over the list of items
                    ]
                    # Assuming there's a mechanism to check for the next page URL in list_data
                    # Example: If the API provides a 'next' key or similar
                    next_page_url = None  # Set this based on actual API response
                else:
                    filtered_list_data = list_data
                    next_page_url = None  # Set this based on actual API response

                return {'results': filtered_list_data, '__next': next_page_url}
            else:
                # Handle the case where list_data is not a list
                raise ValueError("Unexpected data format returned from SharePoint")
        
        except Exception as e:
            raise e