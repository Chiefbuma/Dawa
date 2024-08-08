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
            
            
            #if choice and choice != "Select Month":     
            # get clients sharepoint list
            @st.cache_data(ttl=600, max_entries=100, show_spinner=False, persist=False, experimental_allow_widgets=False)
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
                        "Month",
                        "Cycle"

                ])
                    return pd.DataFrame(clients)
                except APIError as e:
                    st.error("Connection not available, check connection")
                    st.stop() 
            
            cycle_df= load_new()
            
            
            # Get a list of unique values in the 'Cycle' column
            Cycle = cycle_df['Cycle'].unique().tolist()
            
            # Map the month name back to its numeric value
            #month_number = datetime.strptime(choice, "%B").month
                
            cols = st.columns([4,1])
            with cols[0]:
                ui.card(
                        content="Dawa Nyumbani Dashboard",
                        key="MCcard3"
                    ).render()
            with cols[1]:
                with st.container():
                        Cycle_label = "Select Cycle"
                        st.markdown(
                                f"""
                                <div style="background-color:white; padding:10px; border-radius:10px; width:270px; margin-bottom:5px;">
                                    <div style="font-size:18px; font-weight:bold; color:black;">
                                        {Cycle_label}
                                    </div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                
                        choice = ui.select(options=Cycle)
                        
                        if choice :
                                
                            AllMain_df=load_new()   
                                
                            Main_df=AllMain_df[AllMain_df['Cycle'] == choice]
                    
            with card_container(key="Main1"):
                
                
                # Create a new column that indicates whether the CollectionStatus is 'Fully'
                Main_df['Full_Collection'] = Main_df['Collection status'].isin(['Full']).astype(int)
                
                # Create a new column that indicates whether the CollectionStatus is 'Fully'
                Main_df['Partial_Collection'] = Main_df['Collection status'].isin(['Partial']).astype(int)
                
                # Create a new column that indicates whether the CollectionStatus is 'Fully'
                #Main_df['Returned'] = Main_df['Received'] == 'Returned'
                
                
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
                    'Partial_Collection':'Partial',
                    'Full_Collection':'Full',
                    'Collection status': 'Collected',
                    'Month': 'Month',
                    "Cycle":'Cycle'
                })
                
                Consulted_calc = Telesumamry_df [Telesumamry_df['Consulted'] == 'Consulted']
                Consulted= int(Consulted_calc.shape[0])
                
                Dispatched_calc = Telesumamry_df [Telesumamry_df['Dispatched'] == 'Dispatched']
                Dispatched= int(Dispatched_calc.shape[0])
                
                Received_calc = Telesumamry_df [Telesumamry_df['Received'] == 'Received']
                Received= int(Received_calc.shape[0])
                
                Booked_calc = Telesumamry_df [Telesumamry_df['Booked'] == 'Booked']
                Booked= int(Booked_calc.shape[0])

                
                full_calc =Telesumamry_df['Full'].sum()
                Full= full_calc
                
                Partial_calc = Telesumamry_df['Partial'].sum()
                Partial= Partial_calc
                
                #SUMMARY
                #Group by 'Cycle' and count the occurrences for each status
                #Group by 'Cycle' and count the occurrences for each status
                summary_df = Telesumamry_df.groupby('Cycle').agg({
                    'Booked': 'count',
                    'Full':'sum',
                    'Partial':'sum',
                    'Consulted': 'count',
                    'Dispatched': 'count',
                    'Received': 'count'
        
                }).reset_index()

                # Rename columns for clarity (already clear in this case)
                summary_df.columns = [
                    'Cycle', 'Booked', 'Consulted', 'Dispatched', 
                    'Received', 'Full', 'Partial'
                ]

                
                
                #CONSULTED
                # Group by 'Doctor' and count the occurrences for each status
                consulted_df = Telesumamry_df.groupby('Doctor').agg({
                    'Consulted': 'count',
                    'Booked': 'count'
                   
                }).reset_index()
                
                # Calculate Arch%
                consulted_df['Arch%'] = (consulted_df['Consulted'] / consulted_df['Booked'].replace(0, pd.NA)) * 100
                consulted_df = consulted_df.sort_values(by='Arch%', ascending=False)
                consulted_df['Arch%'] = consulted_df['Arch%'].fillna(0)  # Replace NaN with 0
                # Convert to string with % symbol
                consulted_df['Arch%'] = consulted_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                
                
                
                
                #Group by 'Doctor' and count the occurrences for each status
                Received_df = Telesumamry_df.groupby('Medical Centre').agg({
                    'Received': 'count',
                    'Dispatched': 'count'
                }).reset_index()
                
                
                # Calculate Arch%
                Received_df['Arch%'] = (Received_df['Received'] / Received_df['Dispatched'].replace(0, pd.NA)) * 100
                Received_df = Received_df.sort_values(by='Arch%', ascending=False)
                Received_df['Arch%'] = Received_df['Arch%'].fillna(0)  # Replace NaN with 0
                # Convert to string with % symbol
                Received_df['Arch%'] = Received_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                
                
                #Group by 'Doctor' and count the occurrences for each status
                Dispatch_df = Telesumamry_df.groupby('Medical Centre').agg({
                    'Consulted': 'count',
                    'Dispatched': 'count'
                }).reset_index()
                
                # Calculate Arch%
                Dispatch_df['Arch%'] = (Dispatch_df['Consulted'] / Dispatch_df['Dispatched'].replace(0, pd.NA)) * 100
                Dispatch_df = Dispatch_df.sort_values(by='Arch%', ascending=False)
                Dispatch_df['Arch%'] = Dispatch_df['Arch%'].fillna(0)  # Replace NaN with 0
                # Convert to string with % symbol
                Dispatch_df['Arch%'] = Dispatch_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                
            
                #BOOKING
                #Group by 'Doctor' and count the occurrences for each status
                Booking_df = Telesumamry_df.groupby('Cordinator').agg({
                    'Booked': 'count'
                }).reset_index()
                
                # Calculate Arch%
                Booking_df['Target'] = (3921/10)
                
                # Calculate Arch%
                Booking_df['Arch%'] =(Booking_df['Booked'] / Booking_df['Target'].replace(0, pd.NA)) * 100
                Booking_df['Arch%'] = Booking_df['Arch%'].fillna(0)  # Replace NaN with 0
                # Convert to string with % symbol
                Booking_df['Arch%']= Booking_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                
                
            
                #COLLECTION
                #Group by 'Doctor' and count the occurrences for each status
                Collection_df = Telesumamry_df.groupby('Cordinator').agg({
                    'Received': 'count',
                    'Collected': 'count'
                   
                }).reset_index()
                
                                # Calculate Arch%
               
                
             
                
                display_only_renderer = JsCode("""
                    class DisplayOnlyRenderer {
                        init(params) {
                            this.params = params;
                            this.eGui = document.createElement('div');

                            // Set the width and height of the div
                            this.eGui.style.width = '10px'; // Adjust the width as needed
                            this.eGui.style.height = '20px'; // Adjust the height as needed

                            this.eGui.innerText = this.params.value || '';
                        }

                        getGui() {
                            return this.eGui;
                        }
                    }
                    """)
                
                
                display_only_renderer2 = JsCode("""
                    class DisplayOnlyRenderer {
                        init(params) {
                            this.params = params;
                            this.eGui = document.createElement('div');

                            // Set the width and height of the div
                            this.eGui.style.width = 200px'; // Adjust the width as needed
                            this.eGui.style.height = '20px'; // Adjust the height as needed

                            this.eGui.innerText = this.params.value || '';
                        }

                        getGui() {
                            return this.eGui;
                        }
                    }
                    """)



                # This assumes you have a function ui.table to display DataFrames
                #ui.table(data=Received_df, maxHeight=300)
                #st.write(grouped_df)   
            
                coll = st.columns([1,4])
                with coll[0]:
                    colm=st.columns(3)
                    with colm[0]:
                        with st.container():
                                Bok_label = "Booked"
                                st.markdown(
                                    f"""
                                    <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                        <div style="font-size:16px; font-weight:bold; color:black;">
                                            {Bok_label}
                                        </div>
                                        <div style="font-size:20px; font-weight:bold; color:black;">
                                            {Booked}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
    
                        with st.container():
                                Con_label = "Consulted"
                                st.markdown(
                                    f"""
                                    <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                        <div style="font-size:16px; font-weight:bold; color:black;">
                                            {Con_label}
                                        </div>
                                        <div style="font-size:20px; font-weight:bold; color:black;">
                                            {Consulted}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
    
                        with st.container():
                                Dis_label = "Dispatched"
                                st.markdown(
                                    f"""
                                    <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                        <div style="font-size:16px; font-weight:bold; color:black;">
                                            {Dis_label}
                                        </div>
                                        <div style="font-size:20px; font-weight:bold; color:black;">
                                            {Dispatched}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                        with st.container():
                                Rec_label = "Received"
                                st.markdown(
                                    f"""
                                    <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                        <div style="font-size:16px; font-weight:bold; color:black;">
                                            {Rec_label}
                                        </div>
                                        <div style="font-size:20px; font-weight:bold; color:black;">
                                            {Received}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                        with st.container():
                                Collect_label = "Collected"
                                full_label = "Full-"
                                Partial_label = "Partial-"
                                st.markdown(
                                    f"""
                                    <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                        <div style="font-size:16px; font-weight:bold; color:black;">
                                            {Collect_label}
                                        </div>
                                        <div style="font-size:18px; font-weight:bold; color:black;">
                                        {full_label} {Full}
                                        </div>
                                        <div style="font-size:18px; font-weight:bold; color:black;">
                                        {Partial_label}{Partial}
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                        
                with coll[1]:
                        st.markdown("<style> .block-container { padding-top: 0px; } </style>", unsafe_allow_html=True) 
                      
                        selected_option = ui.tabs(options=['Booking','Consultation', 'Receiving', 'Collection'], default_value='', key="reprots")
                        
                        if selected_option == "Consultation":
                            sorted_df=consulted_df
                            st.dataframe(sorted_df, hide_index=True)
                            
                        elif selected_option == "Receiving":
                            sorted_df=Received_df
                            st.dataframe(sorted_df, hide_index=True)
                                
                        elif selected_option == "Collection":
                             sorted_df=Dispatch_df
                             st.dataframe(sorted_df, hide_index=True)
                            
                        elif selected_option == "Booking":
                             sorted_df=Booking_df
                             st.dataframe(sorted_df, hide_index=True)
        else:
            st.write("You  are  not  logged  in. Click   **[Account]**  on the  side  menu to Login  or  Signup  to proceed")
    except APIError as e:
            st.error("Cannot connect, Kindly refresh")
            st.stop() 
            
            
