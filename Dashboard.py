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
from st_aggrid import AgGrid, GridOptionsBuilder,JsCode
from IPython.display import HTML
import conection
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
           
           
            site_url = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"
            username = "biosafety@blisshealthcare.co.ke"
            password = "Streamlit@2024"

            
            def fetch_sharepoint_data():
                try:
                    # Authenticate
                    ctx_auth = AuthenticationContext(site_url)
                    if not ctx_auth.acquire_token_for_user(username, password):
                        st.error("Authentication failed.")
                        return None

                    # Access SharePoint
                    ctx = ClientContext(site_url, ctx_auth)
                    lists = ctx.web.lists.get_by_title("Home Delivery")

                    # Select columns and fetch items
                    query = lists.items.select(
                        "Title",
                        "UHID",
                        "Patientname",
                        "mobile",
                        "Location",
                        "Booking status",
                        "Booking Date",
                        "Booked on",
                        "Booked By",
                        "DoctorName",
                        "Consultation Status",
                        "Consultation Date",
                        "Dispatched status",
                        "Dispatched Date",
                        "Dispatched By",
                        "Received Date",
                        "Received By",
                        "Received Status",
                        "Dispensed By",
                        "Collection status",
                        "Collection Date",
                        "Transfer To",
                        "Transfer Status",
                        "Transfer From",
                        "Month",
                        "Cycle",
                        "MVC"
                        
                    ).get()

                    ctx.execute_query()

                    # Convert items to DataFrame
                    data = [item.properties for item in query]
                    df = pd.DataFrame(data)
                    return df
                except Exception as e:
                    st.error(f"Failed to retrieve data: {e}")
                    return None

            cycle_df = fetch_sharepoint_data()
            
            st.write(cycle_df)
    
        else:
            st.write("You  are  not  logged  in. Click   **[Account]**  on the  side  menu to Login  or  Signup  to proceed")
    except APIError as e:
            st.error("Cannot connect, Kindly refresh")
            st.stop() 
            
            
