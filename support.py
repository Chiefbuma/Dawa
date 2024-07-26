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
import main
from streamlit_dynamic_filters import DynamicFilters
from streamlit_gsheets import GSheetsConnection
from urllib.error import HTTPError
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import gspread
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from postgrest import APIError
from dateutil.relativedelta import relativedelta
from sharepoint import SharePoint



def app():
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False 
        st.write(f"""<span style="color:red;">
                    You are not Logged in,click account to  Log in/Sign up to proceed.
                </span>""", unsafe_allow_html=True)
        
        # Initialize session state if it doesn't exist
                 
    if st.session_state.is_authenticated:
        location=st.session_state.Region
        department=st.session_state.Department
        
        @st.cache_data(ttl=800, max_entries=200, show_spinner=False, persist=False, experimental_allow_widgets=False)
        def load_data():
            try:
                clients = SharePoint().connect_to_list(ls_name='Dawa Nyumbani')
                return pd.DataFrame(clients)
            except APIError as e:
                st.error("Connection not available, check connection")
                st.stop() 
        
        book_df = load_data()
        
        @st.cache_data(ttl=800, max_entries=200, show_spinner=False, persist=False, experimental_allow_widgets=False)
        def load_Trans():
            try:
                clients = SharePoint().connect_to_list(ls_name='MyDawa')
                return pd.DataFrame(clients)
            except APIError as e:
                st.error("Connection not available, check connection")
                st.stop() 
                
        # Initialize GridOptionsBuilder from your dataframe
        Trans_df =  load_Trans()  # Assuming you have a DataFrame named Trans_df
        
        #st.write(Trans_df)
        
        
            # Get unique titles
        Title_names = book_df['Patientname'].unique()

        # Convert to a list if needed
        unique_titles_list = Title_names.tolist()
        #st.write(book_df) 
                
        @st.cache_resource
        def init_connection():
            url = "https://effdqrpabawzgqvugxup.supabase.co"
            key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZmRxcnBhYmF3emdxdnVneHVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA1MTQ1NDYsImV4cCI6MjAyNjA5MDU0Nn0.Dkxicm9oaLR5rm-SWlvGfV5OSZxFrim6x8-QNnc2Ua8"
            return create_client(url, key)

        supabase = init_connection()
        
        # Check if the connection is successful
        if init_connection():
        
            
            st.session_state.logged_in= True
            # Dropdown for selecting the year
        
            #Get the previous month as a date
            previous_month_date = datetime.now() - relativedelta(months=1)

            
            current_month = datetime.now().month 
            current_month_name = datetime.now().strftime("%B")
            current_date=datetime.now().date()
            #current_month = datetime.now() - relativedelta(months=1)
            #current_month_name = (datetime.now() - relativedelta(months=1)).strftime("%B")
            

            
            # Query the MTD_Revenue table with the filter for location_name and Month
            Allresponse = supabase.from_('Dawa_Details').select('*').eq('Medical Centre', location).execute()
            Details_df = pd.DataFrame(Allresponse.data)
            
            #st.write(Details_df)
            
            
            import calendar
            # Query the MTD_Revenue table with the filter for location_name and Month
            response = supabase.table('Patient_Booking').select('*').execute()
            rawbook_df = pd.DataFrame(response.data)
            
            booking_df=rawbook_df[~rawbook_df['Patientname'].isin(unique_titles_list)]
            
           # Add default value for 'Patientname' column where it is empty
            booking_df['Booking Date'] = booking_df['Booking Date'].fillna(current_date)
            
            # Assuming Allsales_df is your DataFrame
            booking_df['Booked on'] = pd.to_datetime(booking_df['Booked on'], dayfirst=True)
            
            booking_df['Booked on'] = booking_df['Booked on'].dt.strftime('%Y-%m-%d')
            
            booking_df['Booked By']=department
            
            # Add 'Month' column with full month name
            booking_df['Month'] = datetime.now().strftime("%B")
            
            # Assuming Allsales_df is your DataFrame
            booking_df['Year'] =  datetime.now().year
                        
            booking_df['Title']=booking_df['Patientname'].astype(str).str.cat(booking_df['Month'])
            

            #st.write(booking_df)
            
            #st.write(booking_df)
            
            # JavaScript function to add a new row to the AgGrid table
            js_add_row = JsCode("""
            function(e) {
                let api = e.api;
                let rowPos = e.rowIndex + 1; 
                api.applyTransaction({addIndex: rowPos, add: [{}]})    
            };
            """     
            )

            # Cell renderer for the '🔧' column to render a button

            # Resources to refer:
            # https://blog.ag-grid.com/cell-renderers-in-ag-grid-every-different-flavour/
            # https://www.w3schools.com/css/css3_buttons.asp

            cellRenderer_addButton = JsCode('''
                class BtnCellRenderer {
                    init(params) {
                        this.params = params;
                        this.eGui = document.createElement('div');
                        this.eGui.innerHTML = `
                        <span>
                            <style>
                            .btn_add {
                                background-color: #71DC87;
                                border: 2px solid black;
                                color: #D05732;
                                text-align: center;
                                display: inline-block;
                                font-size: 12px;
                                font-weight: bold;
                                height: 2em;
                                width: 10em;
                                border-radius: 12px;
                                padding: 0px;
                            }
                            </style>
                            <button id='click-button' 
                                class="btn_add" 
                                >&#x2193; Add</button>
                        </span>
                    `;
                    }
                    getGui() {
                        return this.eGui;
                    }
                };
                ''')
            
            
                        
                        # Custom checkbox renderer
            checkbox_renderer = JsCode("""
                class CheckboxRenderer {
                    init(params) {
                        this.params = params;
                        this.eGui = document.createElement('input');
                        this.eGui.setAttribute('type', 'checkbox');
                        this.eGui.checked = params.value === 'Booked';
                        this.eGui.addEventListener('click', (event) => {
                            if (event.target.checked) {
                                params.setValue('Booked');
                            } else {
                                params.setValue('');
                            }
                        });
                    }

                    getGui() {
                        return this.eGui;
                    }

                    refresh(params) {
                        this.eGui.checked = params.value === 'Booked';
                    }
                }
            """)
            
            
            
                        
            date_renderer = JsCode('''
                class DateRenderer {
                    init(params) {
                        this.params = params;
                        this.eGui = document.createElement('input');
                        this.eGui.type = 'date';
                        if (params.value) {
                            this.eGui.value = params.value;
                        }
                        this.eGui.addEventListener('change', e => {
                            this.params.node.setDataValue(this.params.colDef.field, e.target.value);
                        });
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
            ''')
            
            

            # Create a GridOptionsBuilder object from our DataFrame
            gd = GridOptionsBuilder.from_dataframe(booking_df)

            # List of columns to hide
            hidden_columns = [
                'Booked By',
                'Booking Date',
                'Facility',
                'TeleDoctor',
                'Title',
                'Month',
                'Year'
            ]

            # Hide specified columns
            for col in hidden_columns:
                gd.configure_column(field=col, hide=True,pinned='right')
            
            
            gd.configure_column('Booking status',editable=False, cellRenderer=checkbox_renderer,pinned='right',minWidth=50)
            gd.configure_column("Booked on", editable=False, cellRenderer=date_renderer)
            gd.configure_column('Patientname', editable=False)
            gd.configure_column('UHID', editable=False)
    
            
            
            @st.cache_data
            def get_unique_item_descriptions():
                return booking_df['Location'].unique().tolist()

            # Fetch unique item descriptions
            unique_item_descriptions = get_unique_item_descriptions()
            
            
            
            # Define dropdown options for specified columns
            dropdown_options = {
                'Location': unique_item_descriptions
 
            }
            
            
            for col, options in dropdown_options.items():
                gd.configure_column(field=col, cellEditor='agSelectCellEditor', cellEditorParams={'values': options})
            
            
            # Configure the default column to be editable
            gd.configure_default_column(editable=True,minWidth=150, flex=0)

            # Build the grid options
            gridoptions = gd.build()
            
            
            selected_option = ui.tabs(options=['Booking', 'Dispatch', 'Billing', 'Collection','Dashboard'], default_value='Dashboard', key="kanaries")
                            
        
            # AgGrid Table with Button Feature
            # Streamlit Form helps from rerunning on every widget-click
            # Also helps in providing layout       
            with st.form('Booking') as f:
                st.header('Book a Patient 🔖')
                
            # Inside the form, we are displaying an AgGrid table using the AgGrid function. 
            # The allow_unsafe_jscode parameter is set to True, 
            # which allows us to use JavaScript code in the AgGrid configuration
            # The theme parameter is set to 'balham', 
            # which applies the Balham theme to the table
            # The height parameter is set to 200, 
            # which specifies the height of the table in pixels.
            # The fit_columns_on_grid_load parameter is set to True, 
            # which ensures that the columns of the table are resized to fit 
            # the width of the table when it is first displayed
                
                response = AgGrid(booking_df,
                                gridOptions = gridoptions, 
                                editable=True,
                                allow_unsafe_jscode = True, 
                                theme = 'balham',
                                height = 200,
                                fit_columns_on_grid_load = True)
                
                
                with st.expander("CONFIRM BOKING DETAILS"):
                    
                    try:
                        
                        # Fetch the data from the AgGrid Table
                        res = response['data']
                        #st.table(res)
                        
                        df = pd.DataFrame(res)
                
                                    # Assuming the 'Booking Date' column exists and needs to be formatted
                        if 'Booking Date' in df.columns:
                            df['Booking Date'] = pd.to_datetime(df['Booking Date'], errors='coerce', dayfirst=True)
                            df['Booked on'] = pd.to_datetime(df['Booked on'], errors='coerce', dayfirst=True)
                            df['Booking Date'] = df['Booking Date'].dt.strftime('%d-%m-%Y')
                            df['Booked on'] = df['Booked on'].dt.strftime('%d-%m-%Y')
                        
                        # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                        Appointment_df = df[df['Booking status'] == 'Booked']
                        
                        # Display the filtered DataFrame
                        #st.dataframe(Appointment_df)
                        
                        
                        with card_container(key="Appoint"):
                            cols = st.columns(1)
                            with cols[0]:
                                with card_container(key="table1"):
                                    ui.table(data=Appointment_df, maxHeight=300)
                        
                        cols = st.columns(6)
                        with cols[5]:
                            st.form_submit_button(" Confirm Bookings(s) 🔒", type="primary")
                        
                    
                    except Exception as e:
                        st.error(f"Failed to update to SharePoint: {str(e)}")
                        st.stop() 
                    
                    def submit_to_sharepoint(Appointment_df):
                        try:
                            sp = SharePoint()
                            site = sp.auth()
                            target_list = site.List(list_name='Dawa Nyumbani')

                            # Iterate over the DataFrame and create items in the SharePoint list
                            for ind in Appointment_df.index:
                                item_creation_info = {
                                    'Title': Appointment_df.at[ind, 'Title'],  # Replace 'Title' with your field name
                                    'UHID': Appointment_df.at[ind, 'UHID'],
                                    'Facility': Appointment_df.at[ind, 'Facility'],
                                    'Patientname': Appointment_df.at[ind, 'Patientname'],
                                    'mobile': Appointment_df.at[ind, 'mobile'],
                                    'Location': Appointment_df.at[ind, 'Location'],
                                    'TeleDoctor': Appointment_df.at[ind, 'TeleDoctor'],
                                    'Booking status': Appointment_df.at[ind, 'Booking status'],
                                    'Booking Date': Appointment_df.at[ind, 'Booking Date'],
                                    'Booked on': Appointment_df.at[ind, 'Booked on'],
                                    'Booked By': Appointment_df.at[ind, 'Booked By'],
                                    'Month': Appointment_df.at[ind, 'Month'],
                                    'Year': Appointment_df.at[ind, 'Year']
                                }
                                target_list.UpdateListItems(data=[item_creation_info], kind='New')
                            
                            st.success("Updated to Database", icon="✅")
                        except Exception as e:
                            st.error(f"Failed to update to SharePoint: {str(e)}")
                            st.stop()

            cols=st.columns(12)
            with cols[6]:
                ui_result = ui.button("Clear", key="btn")  
                if ui_result:   
                    st.cache_data.clear()
                    
            with cols[5]:
            # Button to submit DataFrame to SharePoint
                ui_but = ui.button("Submit ", key="subbtn")
                if ui_but:
                    submit_to_sharepoint(Appointment_df)    
        
            #TRANSACTION

            st.write(Trans_df)
            # Filter the DataFrame based on the selected tab
            if selected_option == "Billing" :
                Trans_df = Trans_df[Trans_df['TeleDoctor'] == "Magdalene Wamboi"]
            elif selected_option == "Dispatch" :
                Trans_df = Trans_df[Trans_df['Billing Status'] == "Billed"]
            elif selected_option == "Collection":
                Trans_df = Trans_df[Trans_df['Dispatched status'] == "Dispatched"]

                    # Ensure 'All' option shows the complete DataFrame
            elif selected_option == "All":
                 pass  # #No filtering nee
            
            
           
            gb = GridOptionsBuilder.from_dataframe(Trans_df)

            # List of columns to hide
            book_columns = [
                'Approval Status', 'Level', 'Unique Id', 'Item Type', 'Modified',
                'Property Bag', 'ID', 'owshiddenversion', 'Created', 'Title',
                'Name', 'Effective Permissions Mask', 'ScopeId', 'URL Path',
                'Dispatch Comments', 'Booking status', 'Booking Date', 'Booked on', 'Booked By'
            ]

            # Hide specified columns
            for col in book_columns:
                gb.configure_column(field=col, hide=True, pinned='right')

            # Configure non-editable columns
            non_editable_columns = [
                'Dispatched status', 'Dispatched Date', 'Dispatched By', 'Dispatch Comments',
                'Billing Status', 'Billed Date', 'Billed By', 'Billing Comments',
                'Collection status', 'Collection Date'
            ]
            for column in non_editable_columns:
                gb.configure_column(column, editable=False)

            # Configure specific columns with additional settings
            gb.configure_column('Dispatch Date', editable=False, cellRenderer='checkboxRenderer', pinned='right', minWidth=50)
            gb.configure_column('Billing Status', editable=False, cellRenderer='checkboxRenderer', pinned='right', minWidth=50)
            gb.configure_column('Collection status', editable=False, cellRenderer='checkboxRenderer', pinned='right', minWidth=50)
            gb.configure_column('Dispatched Date', editable=False)
            gb.configure_column('Dispatched By', editable=False)
            gb.configure_column('Billed Date', editable=False)
            gb.configure_column('Billed By', editable=False)
            gb.configure_column('Billing Comments', editable=False)

            # Configure the default column to be editable
            gb.configure_default_column(editable=True, minWidth=150, flex=0)

            # Build the grid options
            gridoptions = gb.build()

            # Streamlit form for dispatch
            with st.form('Dispatch') as f:
                st.header('Dispatch 🔖')

                # Display the AgGrid table
                response2 = AgGrid(
                    Trans_df,
                    gridOptions=gridoptions, 
                    editable=True,
                    allow_unsafe_jscode=True, 
                    theme='balham',
                    height=200,
                    fit_columns_on_grid_load=True
                )

                with st.expander("CONFIRM TRANSACTION DETAILS"):
                    try:
                        # Fetch the data from the AgGrid table
                        res2 = response2['data']
                        Tr = pd.DataFrame(res2)
                        
                        # Display the DataFrame in a table
                        #st.table(Tr)

                        # Submit button within expander
                        cols = st.columns(6)
                        with cols[5]:
                            submit_button = st.form_submit_button("Confirm Transaction(s) 🔒", type="primary")

                        if submit_button:
                            submit_to_sharepoint(Tr)
                    
                    except Exception as e:
                        st.error(f"Failed to update to SharePoint: {str(e)}")
                        st.stop()

            def submit_to_sharepoint(Tr):
                try:
                    sp = SharePoint()
                    site = sp.auth()
                    target_list = site.List(list_name='Dawa Nyumbani')

                    # Iterate over the DataFrame and create items in the SharePoint list
                    for ind in Tr.index:
                        item_creation_info = {
                            'Dispatch Date': Tr.at[ind, 'Dispatch Date'],
                            'Collection Date': Tr.at[ind, 'Collection Date'],
                            'Billed Date': Tr.at[ind, 'Billed Date'],
                            'Dispatched status': Tr.at[ind, 'Dispatched status'],
                            'Dispatched By': Tr.at[ind, 'Dispatched By'],
                            'Billing Status': Tr.at[ind, 'Billing Status'],
                            'Billed By': Tr.at[ind, 'Billed By'],
                            'Collection status': Tr.at[ind, 'Collection status'],
                            'Collection By': Tr.at[ind, 'Collection By']
                        }
                        target_list.UpdateListItems(data=[item_creation_info], kind='Edit')
                    
                    st.success("Updated to Database", icon="✅")
                except Exception as e:
                    st.error(f"Failed to update to SharePoint: {str(e)}")
                    st.stop()

            cols = st.columns(12)
            with cols[6]:
                ui_result = st.button("Clear", key="Transbtn")  
                if ui_result:   
                    st.cache_data.clear()

            with cols[5]:
                # Button to submit DataFrame to SharePoint
                ui_but = st.button("Submit", key="Transubbtn")
                if ui_but:
                    submit_to_sharepoint(Tr)
        
        
        else:
            st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")