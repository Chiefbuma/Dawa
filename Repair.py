import streamlit as st
from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import UserCredential
import streamlit_option_menu as option_menu
import streamlit_shadcn_ui as ui
from local_components import card_container
from streamlit_shadcn_ui import slider, input, textarea, radio_group, switch
from sharepoint import SharePoint
from sharepoint import SharePonitLsist
from postgrest import APIError
from IPython.display import HTML
import conection
import logging
from streamlit_dynamic_filters import DynamicFilters
from st_aggrid import AgGrid, GridOptionsBuilder,JsCode
from office365.sharepoint.listitems.caml.query import CamlQuery



def app():
    
    
    
    
    try:

        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False 
            st.write(f"""<span style="color: red;">
                        You are not Logged in,click account to  Log in/Sign up to proceed.
                    </span>""", unsafe_allow_html=True)
        
            # Initialize session state if it doesn't exist
                    
        if st.session_state.is_authenticated:
            
            
            
             # Credentials and SharePoint URLs
            USERNAME = "biosafety@blisshealthcare.co.ke"
            PASSWORD = "Streamlit@2024"
            SHAREPOINT_SITE = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"
            LIST_NAME = "Maintenance Report"  # The name of the SharePoint list you want to access

            # Authenticate with username and password
            credentials = UserCredential(USERNAME, PASSWORD)
            ctx = ClientContext(SHAREPOINT_SITE).with_credentials(credentials)

            # Get the SharePoint List
            list_object = ctx.web.lists.get_by_title(LIST_NAME)

            # Create an empty list to store all items
            all_items = []

            # CAML query to get list items in batches (pagination)
            caml_query = CamlQuery()
            caml_query.ViewXml = "<View><RowLimit>500</RowLimit></View>"  # Adjust the limit as needed

            # Get first batch of items
            items = list_object.get_items(caml_query)
            ctx.load(items)
            ctx.execute_query()

            # Loop through the results and retrieve all pages
            while True:
                all_items.extend(items)
                if not items.has_next:  # Check if there is a next page
                    break
                items = items.next()
                ctx.load(items)
                ctx.execute_query()

            # Extract the list item properties and convert them to a Pandas DataFrame
            data = [item.properties for item in all_items]
            df = pd.DataFrame(data)

            # Print or process the DataFrame
            print(df)

            # Optional: Ensure all required columns exist (add missing columns if necessary)
            columns = [
                "Date of report", "Name of Staff", "Department", "Month", "Date Number",
                "Clinic", "Departmental report", "Details", "Report", "MainLink flow", "ATTACHED", 
                "MainLINK", "MainItem", "Labor", "Amount on the Quotation", "RIT Approval", 
                "RIT Comment", "RIT labour", "Facility Approval", "Facility comments", 
                "Facility Labor", "Time Line", "Projects Approval", "Project Comments", 
                "Project Labor", "Admin Approval", "Admin Comments", "Admin labor", 
                "Approved amount", "Finance Amount", "STATUS", "Approver", "TYPE", "Days", 
                "Disbursement", "MainStatus", "Modified", "Modified By", "Created By", 
                "ID", "Email", "MAINTYPE", "Attachments", "LinkEdit", "UpdateLink", 
                "PHOTOS", "QUOTES", "Title", "MonthName", "Centre Manager Approval", 
                "Biomedical Head Approval"
            ]

            # Ensure all columns are present
            for col in columns:
                if col not in df.columns:
                    df[col] = None

            # Now 'df' contains the SharePoint list data
            
        else:
            st.write("You  are  not  logged  in. Click   **[Account]**  on the  side  menu to Login  or  Signup  to proceed")
    
    
    except APIError as e:
            st.error("Cannot connect, Kindly refresh")
            st.stop() 
