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
from postgrest import APIError
from IPython.display import HTML
import logs,conection
from streamlit_dynamic_filters import DynamicFilters



def app():
    
    try:

        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False 
            st.write(f"""<span style="color: red;">
                        You are not Logged in,click account to  Log in/Sign up to proceed.
                    </span>""", unsafe_allow_html=True)
        
            # Initialize session state if it doesn't exist
                    
        if st.session_state.is_authenticated:
            
            # get clients sharepoint list
            st.cache_data(ttl=80, max_entries=2000, show_spinner=False, persist=False, experimental_allow_widgets=False)
            def load_new():
                columns = [
                    "Date of report",
                    "Name of Staff",
                    "Department",
                    "Month",
                    "Date Number ",
                    "Clinic",
                    "Departmental report",
                    "Details",
                    "Report",
                    "MainLink flow",
                    "ATTACHED",
                    "MainLINK",
                    "MainItem",
                    "Labor",
                    "Amount on the Quotation",
                    "RIT Approval",
                    "RIT Comment",
                    "RIT labour",
                    "Facility Approval",
                    "Facility comments",
                    "Facility Labor",
                    "Time Line",
                    "Projects Approval",
                    "Project Comments",
                    "Project Labor",
                    "Admin Approval",
                    "Admin Comments",
                    "Admin labor",
                    "Approved amount",
                    "Finance Amount",
                    "STATUS",
                    "Approver",
                    "TYPE",
                    "Days",
                    "Disbursement",
                    "MainStatus",
                    "Modified",
                    "Modified By",
                    "Created By",
                    "ID",
                    "Email",
                    "MAINTYPE",
                    "Attachments",
                    "LinkEdit",
                    "UpdateLink",
                    "PHOTOS",
                    "QUOTES",
                    "Title",
                    "MonthName",
                    "Centre Manager Approval",
                    "Biomedical Head Approval"

                ]
                
                try:
                    clients = SharePoint().connect_to_list(ls_name='Maintenance Report', columns=columns)
                    df = pd.DataFrame(clients)
                    
                    # Ensure all specified columns are in the DataFrame, even if empty
                    for col in columns:
                        if col not in df.columns:
                            df[col] = None

                    return df
                except APIError as e:
                    st.error("Connection not available, check connection")
                    st.stop()
                    
            Main_df = load_new()
            
            
        else:
            st.write("You  are  not  logged  in. Click   **[Account]**  on the  side  menu to Login  or  Signup  to proceed")
    
    
    except APIError as e:
            st.error("Cannot connect, Kindly refresh")
            st.stop() 
