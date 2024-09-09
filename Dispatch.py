import streamlit as st
from st_supabase_connection import SupabaseConnection
from supabase import create_client
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


import json
import os

def app():
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
        st.write(f"""<span style="color:red;">
                    You are not Logged in, click account to Log in/Sign up to proceed.
                </span>""", unsafe_allow_html=True)
        
    if st.session_state.is_authenticated:
        location=st.session_state.Region
        staffnumber=st.session_state.staffnumber
        department = st.session_state.Department
        
    
        
        def get_client_context():
            # Ensure the SharePoint URL is correct
            sharepoint_url = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"
            username = "biosafety@blisshealthcare.co.ke"
            password = "Streamlit@2024"
            list_name = 'Home DeliveryCheck'
            
            # Create authentication context
            ctx_auth = AuthenticationContext(sharepoint_url)
            
            if ctx_auth.acquire_token_for_user(username, password):
                # Create SharePoint context using the valid URL
                ctx = ClientContext(sharepoint_url, ctx_auth)
                web = ctx.web
                ctx.load(web)
                ctx.execute_query()
                st.write(f"Connected to SharePoint site: {web.properties['Title']}")
                
                # Access the SharePoint list by name
                target_list = ctx.web.lists.get_by_title(list_name)
                ctx.load(target_list)
                ctx.execute_query()
                
                st.write(f"Connected to SharePoint list: {list_name}")
                return ctx, target_list
            else:
                st.error(f"Authentication failed: {ctx_auth.get_last_error()}")
                return None, None

        # Function to add an item to SharePoint list
        def add_item_to_sharepoint(ctx, target_list, row):
            item_creation_info = ListItemCreationInformation()
            new_item = target_list.add_item(item_creation_info)
            for key, value in row.items():
                new_item.set_property(key, value)
            new_item.update()
            ctx.execute_query()


        # Function to read last processed row from a file (to avoid duplication)
        def read_last_processed_row():
            last_processed_file = 'last_processed_row.txt'
            if os.path.exists(last_processed_file):
                with open(last_processed_file, 'r') as file:
                    return int(file.read().strip())
            return -1

        # Function to write the last processed row to a file
        def write_last_processed_row(index):
            last_processed_file = 'last_processed_row.txt'
            with open(last_processed_file, 'w') as file:
                file.write(str(index))

        def process_and_upload_to_sharepoint(df):
            # Get the SharePoint context and list
            ctx, target_list = get_client_context()
            if ctx and target_list:
                retries = 3
                start_index = read_last_processed_row() + 1

                for index in range(start_index, len(df)):
                    row = df.iloc[index].to_dict()  # Convert row to dictionary for easier processing
                    for attempt in range(retries):
                        try:
                            # Add item to SharePoint list
                            add_item_to_sharepoint(ctx, target_list, row)  # Pass row as argument
                            
                            st.write(f"Inserted row {index + 1} into the SharePoint list.")
                            write_last_processed_row(index)
                            break
                        except Exception as e:
                            st.error(f"Attempt {attempt + 1} to insert row {index + 1} failed: {e}")
                            if attempt < retries - 1:
                                time.sleep(5)
                            else:
                                st.error(f"Failed to insert row {index + 1} after {retries} attempts.")
                                return

        # Streamlit UI for Excel upload and processing
        st.title("Excel Upload to SharePoint")

        # Upload Excel file widget
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

        # If a file is uploaded
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)

           

            # Replace NaN values with blank strings
            df = df.fillna('').astype(str)

            # Display the DataFrame to the user
            st.write("Uploaded Data Preview:")
            st.write(df)

            # Submit button to trigger the upload to SharePoint
            if st.button("Submit to SharePoint"):
                process_and_upload_to_sharepoint(df)
                st.success("Data submitted successfully.")
        else:
            st.write("Please upload an Excel file to proceed.")
              
    else:
        st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")
