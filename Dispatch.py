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
        
            
        # Excel file path
        excel_file_path =r'C:\Users\Buma\Desktop\Dispacth2.xlsx'

        # Read the Excel file
        df = pd.read_excel(excel_file_path)



        df = df.fillna('') 

        # Convert all columns to strings
        df = df.astype(str)


        print(df)
        # Replace NaN values with blank strings in the entire DataFrame
        
        
            
        # Constants for SharePoint
        sharepoint_url = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"
        username = "biosafety@blisshealthcare.co.ke"
        password = "Streamlit@2024"
        list_name = 'Home DeliveryCheck'


        # Connect to SharePoint
        ctx_auth = AuthenticationContext(sharepoint_url)
        if ctx_auth.acquire_token_for_user(username, password):
            ctx = ClientContext(sharepoint_url, ctx_auth)
            web = ctx.web
            ctx.load(web)
            ctx.execute_query()
            print(f"Connected to SharePoint site: {web.properties['Title']}")
        else:
            print(ctx_auth.get_last_error())

        def process_and_upload_to_sharepoint(df):
            # Get the SharePoint list
            target_list = ctx.web.lists.get_by_title(list_name)
            ctx.load(target_list)
            ctx.execute_query()

            # Insert rows into the SharePoint list
            for index, row in df.iterrows():
                item_creation_info = row.to_dict()
                target_list.add_item(item_creation_info).execute_query()
                print(f"Inserted row {index + 1} into the list.")
            
            return  

        print("All rows have been inserted.")
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
