import streamlit as st
from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
import streamlit_option_menu as option_menu
from st_aggrid import AgGrid, GridOptionsBuilder,JsCode
from sharepoint import SharePoint
from local_components import card_container
import streamlit.components.v1 as components
import streamlit_shadcn_ui as ui
import logging
from postgrest import APIError
from shareplum import Site, Office365
from shareplum.site import Version
import pandas as pd
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list  import ListItemCreationInformation
from office365.sharepoint.lists.list import List
import time
import os

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
def app():
    
    # Check if user is authenticated
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
        st.write("""<span style="color:red;">
                    You are not Logged in, click account to Log in/Sign up to proceed.
                </span>""", unsafe_allow_html=True)
        
    if st.session_state.is_authenticated:
        location = st.session_state.Region
        staffnumber = st.session_state.staffnumber
        department = st.session_state.Department

        # Supabase credentials
        url = "https://effdqrpabawzgqvugxup.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZmRxcnBhYmF3emdxdnVneHVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA1MTQ1NDYsImV4cCI6MjAyNjA5MDU0Nn0.Dkxicm9oaLR5rm-SWlvGfV5OSZxFrim6x8-QNnc2Ua8"
        supabase: Client = create_client(url, key)

        with card_container("Upload"):
            st.header('Dispatch Packages🔖')
             # Upload Excel file
             # Upload CSV file
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

            if uploaded_file is not None:
                # Load CSV file into DataFrame
                df = pd.read_csv(uploaded_file)

                # Replace 'None' values (if any) and NaN values with blank strings and convert columns to strings
                df = df.fillna('').replace('None', '').astype(str)
                

                current_date = datetime.now().date()
                formatted_date = current_date.strftime("%d/%m/%Y")
                
                # Modify the DataFrame
                df['Dispatched Date'] = df['Dispatched Date'].fillna(formatted_date)
                df['Dispatched By'] = department
                df['Transaction Type'] = "Dispatch"
                
                # Display the DataFrame to the user
                st.write("Uploaded Data Preview:")
                st.dataframe(df)

                # Submit button
                if st.button("Submit"):
                    
                    max_attempts = 3  # Maximum number of attempts
                    attempt = 0  # Start at attempt 0
                    success = False  # Track success
                    
                    for attempt in range(max_attempts):
                        try:
                            with st.spinner('Submitting...'):
                                # Insert the entire DataFrame at once into the 'Home_Delivery' table
                                response = supabase.table("Home_Delivery").insert(df.to_dict(orient='records')).execute()
                                
                                st.write(f"{len(df)} rows inserted successfully.")
                            
                            break
                        
                        except Exception as e:
                            
                            
                            response = supabase.table("Home_Delivery").insert(df.to_dict(orient='records')).execute()
                            # Access error code and message for precise handling
                            error_code = response.error.get('code')
                            error_message = response.error.get('message')
                            
                            # Display error message for the current attempt
                            st.write(f"Attempt {attempt}: Failed to insert rows. Error Code: {error_code}, Message: {error_message}")
                            
                            if attempt < max_attempts - 1:
                                time.sleep(5)
                                # Insert the entire DataFrame at once into the 'Home_Delivery' table
                                response = supabase.table("Home_Delivery").insert(df.to_dict(orient='records')).execute()
                                
                                st.write(f"{len(df)} rows inserted successfully.")
                                
                                break
                        
                            else:
                                st.error(f"Failed to insert items after {attempt} attempts.")
                                return
                else:
                  st.write("Please upload an Excel file to proceed.")
                   

if __name__ == "__main__":
    app()