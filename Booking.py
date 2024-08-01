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
from streamlit_dynamic_filters import DynamicFilters
from urllib.error import HTTPError
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from postgrest import APIError
from dateutil.relativedelta import relativedelta
from sharepoint import SharePoint
import conection
import logs


def app():
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False 
        st.write(f"""<span style="color:red;">
                    You are not Logged in,click account to  Log in/Sign up to proceed.
                </span>""", unsafe_allow_html=True)
        
        # Initialize session state if it doesn't exist
                 
    if st.session_state.is_authenticated:
        location=st.session_state.Region
        staffnumber=st.session_state.staffnumber
        department = st.session_state.Department
        
        @st.cache_data(ttl=80, max_entries=2000, show_spinner=False, persist=False, experimental_allow_widgets=False)
        def load_new():
                try:
                    clients = SharePoint().connect_to_list(ls_name='Home Delivery',columns=[
                        "Title",
                        "ID",
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
                        "MVC",
                        "Cycle",
                        "Collection Comments",
                        "Transaction Type",
                        "Year"

])
                    return pd.DataFrame(clients)
                except APIError as e:
                    st.error("Connection not available, check connection")
                    st.stop() 
            
        book_df= load_new()
        
        #st.write(book_df)
        
        Max_df = book_df.groupby('Patientname', as_index=False).agg(
                 Max_Cycle=('Cycle', 'max')
        )
        
        
        #st.write(Max_df)
        
        #st.write(book_df)
        # Get unique titles
        #Title_names = book_df['Patientname'].unique()

        # Convert to a list if needed
        #unique_titles_list = Title_names.tolist()
        #st.write(book_df) 
                
        @st.cache_resource
        def init_connection():
            url = "https://effdqrpabawzgqvugxup.supabase.co"
            key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZmRxcnBhYmF3emdxdnVneHVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA1MTQ1NDYsImV4cCI6MjAyNjA5MDU0Nn0.Dkxicm9oaLR5rm-SWlvGfV5OSZxFrim6x8-QNnc2Ua8"
            return create_client(url, key)

        supabase = init_connection()
        
        
        #st.write(Details_df)
            

        
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
            formatted_date = current_date.strftime("%d/%m/%Y")

            
            # Query the MTD_Revenue table with the filter for location_name and Month
            Allresponse = supabase.from_('Dawa_Details').select('*').execute()
            Details_df = pd.DataFrame(Allresponse.data)
            
                   
            response = supabase.from_('usersD').select('*').eq('staffnumber', staffnumber).execute()
            usersD_df = pd.DataFrame(response.data)
            
            staffname = usersD_df['staffname'].iloc[0]
            
            #st.write(staffname)
            import calendar
            # Query the MTD_Revenue table with the filter for location_name and Month
            response = supabase.table('Patient_Booking').select('*').execute()
            rawbook_df = pd.DataFrame(response.data)
            
            #st.write(rawbook_df)
            # Merge Max_df onto rawbook_df along 'Patientname'
            
            booking_df = rawbook_df.merge(Max_df, on='Patientname', how='left')
            
            #st.write(booking_df)

            
           # Add default value for 'Patientname' column where it is empty
            booking_df['Booking Date'] = booking_df['Booking Date'].fillna(formatted_date)
            
            
            booking_df['Max_Cycle'] = booking_df['Max_Cycle'].fillna(1)
            
            # Assuming Allsales_df is your DataFrame
            booking_df['Booked on'] = pd.to_datetime(booking_df['Booked on'], dayfirst=True)
            
            booking_df['Booked on'] = booking_df['Booked on']
            
            booking_df['Booked By']=staffname
            
            booking_df['Cycle'] = booking_df['Max_Cycle'].astype(int)+1
            
            # Add 'Month' column with full month name
            booking_df['Month'] = datetime.now().strftime("%B")
            
            # Assuming Allsales_df is your DataFrame
            booking_df['Year'] =  datetime.now().year
                        
            booking_df['Title']=booking_df['Patientname'].astype(str)  + booking_df['Month']  + booking_df['Cycle'].astype(str)
            
            booking_df['TransactionType'] ="Booking"
            

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

            # Define JavaScript code for the custom dropdown renderer
            
            
            # Define the list of names for the dropdown
            names_list = [
                "Abdalla Said",
                "Alfred Kalisa",
                "Alya Shalima",
                "Bancy  Mbogo",
                "Barbra Mumbi",
                "BRIAN MURIUKI",
                "David  Gikobi",
                "Denis Kiplangat",
                "Diana Bonareri",
                "DoctorName",
                "Edwin Wangila",
                "Elizabeth  Pratice Waithera",
                "Francis Abuga",
                "Grace  Nasike",
                "Grace Githaga",
                "Jezreel Kagunda",
                "John  Wachira",
                "Kendra  Ochieng",
                "Kenneth Nkunja Muiruri",
                "Kinita  Patel",
                "Margaret Wangari Kiniya",
                "Martha Njoki",
                "Melissa Muthoni",
                "Mohammed Nurr",
                "Nebart Nyaga",
                "Nuru Jumaan",
                "Sheila Kisiangani",
                "Shruti  Sandeep",
                "Solomon   Mwendwa",
                "Susan Opondo",
                "Terry   Kariuki",
                "Victor Maweu",
                "Yuvy Nalse Mochama"

            ]
            dropdown_renderer = JsCode(f"""
            class DropdownRenderer {{
                init(params) {{
                    this.params = params;
                    this.eGui = document.createElement('select');

                    // Add an empty option as the default
                    let emptyOption = document.createElement('option');
                    emptyOption.value = '';
                    emptyOption.innerHTML = '--Select--';
                    this.eGui.appendChild(emptyOption);

                    // Add options from the predefined list
                    const options = {names_list};
                    options.forEach(option => {{
                        let optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.innerHTML = option;
                        this.eGui.appendChild(optionElement);
                    }});

                    this.eGui.value = this.params.value || '';

                    this.eGui.addEventListener('change', (event) => {{
                        this.params.setValue(event.target.value);
                    }});
                }}

                getGui() {{
                    return this.eGui;
                }}
            }}
            """)

            
            
                        
            # Custom checkbox renderer
            checkbox_renderer = JsCode("""
            class CheckboxRenderer {
                init(params) {
                    this.params = params;
                    this.eGui = document.createElement('input');
                    this.eGui.setAttribute('type', 'checkbox');
                    
                    // Default the checkbox to unchecked
                    this.eGui.checked = params.value === '';
                    
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
                    // Update the checkbox state when the cell is refreshed
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
                            
                            // Set the date value to the provided value or default to empty if not provided
                            this.eGui.value = params.value || '';  // Default to empty if params.value is undefined or null
                            
                            // Add event listener for change events
                            this.eGui.addEventListener('change', e => {
                                const newValue = e.target.value || '';  // Ensure empty string if no value is selected
                                this.params.node.setDataValue(this.params.colDef.field, newValue);
                            });
                        }

                        getGui() {
                            return this.eGui;
                        }

                        refresh(params) {
                            // Update the date input value on refresh
                            this.eGui.value = params.value || '';  // Default to empty if params.value is undefined or null
                        }
                    }
                ''')

            

            # Create a GridOptionsBuilder object from our DataFrame
            gd = GridOptionsBuilder.from_dataframe(booking_df)
            
             # Configure the default column to be editable
            gd.configure_default_column(editable=True,minWidth=150, flex=0,filter=True)

            # List of columns to hide
            hidden_columns = [
                'Booked By',
                'Booking Date',
                'Location',
                'TeleDoctor',
                'Title',
                'TransactionType',
                'Month',
                'MVC',
                'Max_Cycle',
                'Collection Comments',
                'Year',
                'S.No'
            ]
            
             # Configure non-editable columns
            non_editable_columns = [
                    "UHID",
                    "Patientname",
                    "Location",
                    "Cycle",
          
          
            ]
            for column in non_editable_columns:
                gd.configure_column(column, editable=False)

           # Configure the 'DoctorName' column with the dropdown renderer
            gd.configure_column('DoctorName', cellEditor='agSelectCellEditor', cellEditorParams={'values': names_list}, cellRenderer=dropdown_renderer)

            
            # Hide specified columns
            for col in hidden_columns:
                gd.configure_column(field=col, hide=True,pinned='right')
            
            
            gd.configure_column('Booking status',editable=False, cellRenderer=checkbox_renderer,pinned='right',minWidth=50)
            gd.configure_column("Booked on", editable=False, cellRenderer=date_renderer)
            gd.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gd.configure_column('UHID', editable=False,filter="agTextColumnFilter")
    
           
            # Build the grid options
            gridoptions = gd.build()
         
            # AgGrid Table with Button Feature
            # Streamlit Form helps from rerunning on every widget-click
            # Also helps in providing layout  
                 
            with st.form('Booking Patient') as f:
                st.header('Book  Patient🔖')
                
                response = AgGrid(booking_df,
                                gridOptions = gridoptions, 
                                editable=True,
                                allow_unsafe_jscode = True, 
                                theme = 'balham',
                                height = 200,
                                fit_columns_on_grid_load = True)

                
                cols = st.columns(6)
                with cols[5]:
                    st.form_submit_button(" Confirm Booking(s) 🔒", type="primary")
                
            with card_container(key="Main1"):
                try:
                    
                    # Fetch the data from the AgGrid Table
                    res = response['data']
                    #st.table(res)
                    
                    df = pd.DataFrame(res)
            
                    # Assuming the 'Booking Date' column exists and needs to be formatted
                    if 'Booking Date' in df.columns:
                        df['Booking Date'] = pd.to_datetime(df['Booking Date'], errors='coerce', dayfirst=True)
                        df['Booked on'] = pd.to_datetime(df['Booked on'], errors='coerce', dayfirst=True)
                        df['Booking Date'] = df['Booking Date'].dt.strftime('%d/%m/%Y')
                        df['Booked on'] = df['Booked on'].dt.strftime('%d/%m/%Y')
                    
                    # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                    Appointment_df = df[df['Booking status'] == 'Booked']
                    
                    #st.write(Appointment_df)
                    
                    Appointment_df=Appointment_df[['Title','UHID',	'Patientname','mobile','DoctorName','Booking status','Booking Date',	
                                    'Booked on','Booked By'	,'Month','Year','TransactionType','Cycle']]

                    
                    # Display the filtered DataFrame
                    #st.dataframe(Appointment_df)
                    
                    
                    with card_container(key="Appoint"):
                        cols = st.columns(1)
                        with cols[0]:
                            with card_container(key="table1"):
                                ui.table(data=Appointment_df, maxHeight=300)
                    
                
                except Exception as e:
                    st.error(f"Failed to update to SharePoint: {str(e)}")
                    st.stop()
                    
               
                def validate_appointment_data(df):
                    
                    """
                    Validate the Appointment_df DataFrame to check for blank 'DoctorName' fields.
                    Returns a boolean indicating if the data is valid and a list of row indices with issues.
                    """
                    invalid_rows = df[df['DoctorName'] == "None"].index.tolist()
                    if invalid_rows:
                        return False, invalid_rows
                    return True, []

                def submit_to_sharepoint(Appointment_df):
                    # Validate data before submission
                    is_valid, invalid_rows = validate_appointment_data(Appointment_df)
                    
                    if not is_valid:
                        st.error(f"'DoctorName' is blank in rows: {invalid_rows}")
                        return

                    try:
                        with st.spinner('Submitting...'):
                            sp = SharePoint()
                            site = sp.auth()
                            target_list = site.List(list_name='Home Delivery')

                            # Iterate over the DataFrame and create items in the SharePoint list
                            for ind in Appointment_df.index:
                                item_creation_info = {
                                    'Title': Appointment_df.at[ind, 'Title'],  # Replace 'Title' with your field name
                                    'UHID': Appointment_df.at[ind, 'UHID'],
                                    'Patientname': Appointment_df.at[ind, 'Patientname'],
                                    'mobile': Appointment_df.at[ind, 'mobile'],
                                    'DoctorName': Appointment_df.at[ind, 'DoctorName'],
                                    'Booking status': Appointment_df.at[ind, 'Booking status'],
                                    'Booking Date': Appointment_df.at[ind, 'Booking Date'],
                                    'Booked on': Appointment_df.at[ind, 'Booked on'],
                                    'Booked By': Appointment_df.at[ind, 'Booked By'],
                                    'Transaction Type': Appointment_df.at[ind, 'TransactionType'],
                                    'Month': Appointment_df.at[ind, 'Month'],
                                    'Year': Appointment_df.at[ind, 'Year'],
                                    'Cycle': Appointment_df.at[ind, 'Cycle']
                                }
                                target_list.UpdateListItems(data=[item_creation_info], kind='New')
                            
                            st.success("Succesfully submitted", icon="✅")
                    except Exception as e:
                        st.error(f"Failed to update to SharePoint: {str(e)}")
                        st.stop()



            cols=st.columns(4)
            with cols[2]:
            # Button to submit DataFrame to SharePoint
                ui_but = ui.button("Submit ", key="subbtn")
                if ui_but:
                    submit_to_sharepoint(Appointment_df)    
              
        else:
            st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")
