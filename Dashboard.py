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
            
            def get_month_options():
                current_year = datetime.now().year
                current_month = datetime.now().month
                month_names = [
                    datetime(current_year, month, 3).strftime('%B')
                    for month in range(3, current_month + 1)
                ]
                month_names.insert(0, "Select Month")
                return month_names

            month_options = get_month_options()
            cols = st.columns(2)
            ui.card(
                    content="Dawa Nyumbani Dashboard",
                    key="MCcard3"
                ).render()

            #if choice and choice != "Select Month":     
            # get clients sharepoint list
            
            def load_new():
                try:
                    clients = SharePoint().connect_to_list(ls_name='Home Delivery',columns=[
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
                        "Month"

                ])
                    return pd.DataFrame(clients)
                except APIError as e:
                    st.error("Connection not available, check connection")
                    st.stop() 
            
            Main_df= load_new()
                    
            # Map the month name back to its numeric value
            #month_number = datetime.strptime(choice, "%B").month
            
            # Renaming columns
            Telesumamry_df = Main_df.rename(columns={
                'DoctorName': 'Doctor',
                'Booked By':'Cordinator',
                'Dispatched By':'WareHouse',
                'Location':'Medical Centre',
                'Dispensed By':'Pharmatech.',
                'Booking status': 'Booked',
                'Consultation Status': 'Consulted',
                'Dispatched status': 'Dispatched',
                'Received Status': 'Received',
                'Collection status': 'Collected',
                'Month': 'Month'
            })
            
            #CONSULTED
            
            # Group by 'Doctor' and count the occurrences for each status
            consulted_df = Telesumamry_df.groupby('Doctor').agg({
                'Booked': 'count',
                'Consulted': 'count'
            }).reset_index()
            
            # Calculate Arch% as the percentage of 'Consulted' against 'Booked'
            consulted_df['Arch%'] = (consulted_df['Booked'] / consulted_df['Consulted']) * 100
            
            # Sort the DataFrame by 'Arch%' in descending order
            sorted_df = consulted_df.sort_values(by='Arch%', ascending=False)
            
            
            #RECEIVED
            
            #Group by 'Doctor' and count the occurrences for each status
            Received_df = Telesumamry_df.groupby('Medical Centre').agg({
                'Dispatched': 'count',
                'Received': 'count'
            }).reset_index()
            
            # Calculate Arch% as the percentage of 'Consulted' against 'Booked'
            Received_df['Arch%'] = (Received_df['Received'] / Received_df['Dispatched']) * 100
            
            # Sort the DataFrame by 'Arch%' in descending order
            Received_df = Received_df.sort_values(by='Arch%', ascending=False)
            
            
            #COLLECTION
            
            #Group by 'Doctor' and count the occurrences for each status
            Collection_df = Telesumamry_df.groupby('Cordinator').agg({
                'Collected': 'count',
                'Received': 'count'
            }).reset_index()
            
            # Calculate Arch% as the percentage of 'Consulted' against 'Booked'
            Collection_df['Arch%'] = (Collection_df['Received'] / Collection_df['Collected']) * 100
            
            # Sort the DataFrame by 'Arch%' in descending order
            Collection_df = Collection_df.sort_values(by='Arch%', ascending=False)
            
            #st.write(grouped_df)
            with card_container(key="DOCS"):
                cols=st.columns(2)
                with cols[1]:
                        st.markdown("<style> .block-container { padding-top: 0px; } </style>", unsafe_allow_html=True) 
                        with card_container(key="table1"):
                            selected_option = ui.tabs(options=['Consulted vs Booked', 'Received vs Discpatched', 'Collected vs Received'], default_value='', key="kanaries")
                            
                            if selected_option == "Consulted vs Booked":
                                sorted_df=consulted_df
             
                            elif selected_option == "Received vs Discpatched":
                                sorted_df=Received_df
                                    
                            elif selected_option == "Collected vs Received":
                                 sorted_df=Collection_df
 
                            # Configure GridOptions for the main grid
                            gb = GridOptionsBuilder.from_dataframe(sorted_df)
                            
                            # Configure the default column to be editable
                            gb.configure_default_column(editable=True, minWidth=10, flex=0)

                            # Build the grid options
                            gridoptions = gb.build()
                            
                            
                            response = AgGrid(
                                            sorted_df,
                                            gridOptions=gridoptions,
                                            editable=True,
                                            allow_unsafe_jscode=True,
                                            theme='balham',
                                            height=300,
                                            width=5,
                                            fit_columns_on_grid_load=True)

    except APIError as e:
                st.error("Cannot connect, Kindly refresh")
                st.stop() 
