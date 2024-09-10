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


# Constants for SharePoint
sharepoint_url = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"
username = "biosafety@blisshealthcare.co.ke"
password = "Streamlit@2024"
list_name = 'Home DeliveryCheck'

def connect_to_sharepoint():
    ctx_auth = AuthenticationContext(sharepoint_url)
    if ctx_auth.acquire_token_for_user(username, password):
        ctx = ClientContext(sharepoint_url, ctx_auth)
        web = ctx.web
        ctx.load(web)
        ctx.execute_query()
        return ctx
    else:
        st.error(f"Failed to authenticate: {ctx_auth.get_last_error()}")
        return None

def upload_to_sharepoint(df, ctx):
    retries = 3
    if ctx is None:
        st.error("No connection to SharePoint.")
        return

    try:
        # Get the SharePoint list
        target_list = ctx.web.lists.get_by_title(list_name)
        ctx.load(target_list)
        ctx.execute_query()

        # Fetch existing items from the SharePoint list
        existing_items = target_list.get_items().execute_query()
        existing_data = {item.properties['Title'] for item in existing_items}  # Adjust based on your unique identifier

        # Prepare new items to be inserted
        new_items = []
        for index, row in df.iterrows():
            item_creation_info = row.to_dict()
            
            # Ensure the values are strings and handle empty values
            for key, value in item_creation_info.items():
                if value is None or pd.isna(value):
                    item_creation_info[key] = ""
                else:
                    item_creation_info[key] = str(value)

            # Check for duplicates based on a unique field (e.g., 'Title')
            if item_creation_info.get('Title') not in existing_data:
                new_items.append(item_creation_info)

        # Insert new rows into the SharePoint list
        for item_creation_info in new_items:
            for attempt in range(retries):
                try:
                    target_list.add_item(item_creation_info).execute_query()
                    st.write(f"Inserted  {index} {item_creation_info.get('Title')} into SharePoint.")
                    break
                except Exception as e:
                    st.error(f"Attempt {attempt + 1} to insert item with Title {item_creation_info.get('Title')} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(5)
                        # Reconnect on failure
                        ctx = connect_to_sharepoint()
                        if not ctx:
                            st.error("Reconnection failed. Exiting.")
                            return
                        target_list = ctx.web.lists.get_by_title(list_name)
                        ctx.load(target_list)
                        ctx.execute_query()
                    else:
                        st.error(f"Failed to insert item with Title {item_creation_info.get('Title')} after {retries} attempts.")
                        return

        st.success("All new rows have been inserted successfully.")
    except Exception as e:
        st.error(f"Failed to upload to SharePoint: {str(e)}")


        st.success("All rows have been inserted successfully.")
    except Exception as e:
        st.error(f"Failed to upload to SharePoint: {str(e)}")

def app():
    
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
        st.write(f"""<span style="color:red;">
                    You are not Logged in, click account to Log in/Sign up to proceed.
                </span>""", unsafe_allow_html=True)
        
    if st.session_state.is_authenticated:
        location = st.session_state.Region
        staffnumber = st.session_state.staffnumber
        department = st.session_state.Department
        
        # Format the date as a string (e.g., YYYY-MM-DD)
        current_date = datetime.now().date()
        formatted_date = current_date.strftime("%d/%m/%Y")
        
        with st.expander("Upload dispatch"):
    
            uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

            if uploaded_file is not None:
                df = pd.read_excel(uploaded_file)

                # Convert date columns to the required format
                date_columns = ['BookingDate', 'ConsultationDate', 'DispatchedDate', 'ReceivedDate', 'CollectionDate', 'Booked on']
                available_date_columns = [col for col in date_columns if col in df.columns]
                
                for column in available_date_columns:
                    df[column] = pd.to_datetime(df[column]).dt.strftime('%d/%m/%Y')

                # Replace NaN values with blank strings and convert columns to strings
                df = df.fillna('').astype(str)

                
                # Modify the DataFrame
                df['DispatchedDate'] = df['DispatchedDate'].fillna(formatted_date)
                df['DispatchedBy'] = department
                df['DispatchedBy'] = staffnumber
                df['TransactionType'] = "Dispatch"
                
                st.markdown("""
                    <style>
                        .stExpander, .stContainer {
                        margin-bottom: 0px; /* Adjust bottom margin to create space between widgets */
                        }
                        .stExpander, .stContainer {
                        padding: 0px; /* Optional: Add padding inside the widget */
                        }
                    </style>
                    """, unsafe_allow_html=True)
                        
                with card_container(key="disp"):
                    
                    try:
                        
                    # Display the DataFrame to the user
                        st.write("Uploaded Data Preview:")
                        st.dataframe(df)
                    
                    except Exception as e:
                        st.error(f"Failed to update to SharePoint: {str(e)}")
                        st.stop() 
                
                # Display DataFrame in an editable grid (optional code omitted for brevity)
                
                #SUMMARY
                #Group by 'Cycle' and count the occurrences for each status
                summary_df = df.groupby(['Location','Cycle']).agg({
                    'BookingStatus':'count',
                    'ConsultationStatus': 'count',
                    'ConsultationStatus': 'count',
                    'Dispatchedstatus': 'count'
                
        
                }).reset_index()
                
                
                with card_container(key="dis"):
                    
                    try:
                        
                    # Display the DataFrame to the user
                        st.write("Uploaded Data Preview:")
                        st.dataframe(summary_df)
                    
                    except Exception as e:
                        st.error(f"Failed to update to SharePoint: {str(e)}")
                        st.stop() 
                

                # Submit button to trigger the upload to SharePoint
                if st.button("Submit to SharePoint"):
                    ctx = connect_to_sharepoint()
                    upload_to_sharepoint(df, ctx)
            else:
                st.write("Please upload an Excel file to proceed.")   
        
        with st.expander("EDIT DISPATCH"):
           
            #AllTrans_df = load_data(email_user, password_user, sharepoint_url, list_name)
            @st.cache_data(ttl=80, max_entries=2000, show_spinner=False, persist=False, experimental_allow_widgets=False)
            def load_new():
                columns = [
                    "Title", "ID", "UHID", "Patientname", "mobile", "Location", "Booking status", 
                    "Booking Date", "Booked on", "Booked By", "DoctorName", "Consultation Status", 
                    "Consultation Date", "Dispatched status", "Dispatched Date", "Dispatched By", 
                    "Received Date", "Received By","Received Comments", "Received Status", "Dispensed By", "Collection status", 
                    "Collection Date", "MVC", "Cycle", "Collection Comments", "Month", 
                    "Transaction Type", "Year"
                ]
                
                try:
                    clients = SharePoint().connect_to_list(ls_name='Home Delivery', columns=columns)
                    df = pd.DataFrame(clients)
                    
                    # Ensure all specified columns are in the DataFrame, even if empty
                    for col in columns:
                        if col not in df.columns:
                            df[col] = None

                    return df
                except APIError as e:
                    st.error("Connection not available, check connection")
                    st.stop()
            
            #st.write(AllTrans_df)
            cycle_df = load_new()
                
            #st.write(cycle_df)
                
            # Get a list of unique values in the 'Cycle' column
            Cycle = cycle_df['Cycle'].unique().tolist()
            
            cols = st.columns([4,1])
            with cols[0]:
                st.header('Collect  Package🔖')
            with cols[1]:
                with st.container():
                                choice = st.selectbox('Select Cycle', Cycle) 
                                if choice :
                                        
                                    mainall = load_new()  
                                        
                                    AllTrans_df=mainall[mainall['Cycle'] == choice]
    
    


            #Set the default date as a string
            default_date = '00/00/0000'

            # Use it directly without applying strftime
            formatted_date = default_date
            
            
            @st.cache_resource
            def init_connection():
                url = "https://effdqrpabawzgqvugxup.supabase.co"
                key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZmRxcnBhYmF3emdxdnVneHVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA1MTQ1NDYsImV4cCI6MjAyNjA5MDU0Nn0.Dkxicm9oaLR5rm-SWlvGfV5OSZxFrim6x8-QNnc2Ua8"
                return create_client(url, key)

            supabase = init_connection()

            if supabase:
                st.session_state.logged_in = True
                previous_month_date = datetime.now() - relativedelta(months=1)
                current_month = datetime.now().month 
                current_month_name = datetime.now().strftime("%B")
                current_date = datetime.now().date()

                Allresponse = supabase.from_('Dawa_Details').select('*').execute()
                Details_df = pd.DataFrame(Allresponse.data)
                
                Allresponse2 = supabase.from_('Chronic_List').select('*').execute()
                chronic_df = pd.DataFrame(Allresponse2.data)
                
                
                response = supabase.from_('usersD').select('*').eq('staffnumber', staffnumber).execute()
                usersD_df = pd.DataFrame(response.data)
                
                staffname = usersD_df['staffname'].iloc[0]
                
                
                Trans_df = AllTrans_df[
                        (AllTrans_df['Dispatched status'] == 'Dispatched') & 
                        (AllTrans_df['Received Status'].isnull())]
                
                
               
                Trans_df['Dispatched By'] = department
                
                Trans_df['Dispatched By']=staffname
                
                Trans_df['Transaction Type']= "Dispatch"
            
                #st.write(staffname)
                #st.write(chronic_df)
                
                # JavaScript for link renderer
                cellRenderer_link = JsCode("""
                class LinkRenderer {
                    init(params) {
                        this.params = params;
                        this.eGui = document.createElement('a');
                        this.eGui.innerHTML = 'View Prescription';
                        this.eGui.href = 'javascript:void(0)';
                        this.eGui.addEventListener('click', () => {
                            const selectedCategory = params.data.Patientname;
                            window.parent.postMessage({ type: 'VIEW_CHILD_GRID', category: selectedCategory }, '*');
                        });
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
                """)

                # JavaScript for checkbox renderer
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
                                    params.setValue('Dispatched');
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
                            this.eGui.checked = params.value === 'Dispatched';
                        }
                    }
                    """)
                
                textarea_renderer = JsCode("""
                    class TextareaRenderer {
                        init(params) {
                            this.params = params;
                            this.eGui = document.createElement('textarea');
                            
                            // Set the width and height of the textarea
                            this.eGui.style.width = '300px'; // Adjust the width as needed
                            this.eGui.style.height = '100px'; // Adjust the height as needed

                            this.eGui.value = this.params.value || '';

                            this.eGui.addEventListener('change', (event) => {
                                this.params.setValue(event.target.value);
                            });
                        }

                        getGui() {
                            return this.eGui;
                        }
                    }
                    """)

                # JavaScript for date renderer
                date_renderer = JsCode("""
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
                """)
                
                response = supabase.table('facilities').select("*").execute()

                location_df = pd.DataFrame(response.data)
                
                @st.cache_data
                def get_unique_item_descriptions():
                    return location_df['Location'].unique().tolist()

                # Fetch unique item descriptions
                unique_item_descriptions = get_unique_item_descriptions()

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
                            const options = {unique_item_descriptions};
                            options.forEach(option => {{
                                let optionElement = document.createElement('option');
                                optionElement.value = option;
                                optionElement.innerHTML = option;
                                this.eGui.appendChild(optionElement);
                            }});

                            this.eGui.value = this.params.value || '';

                            // Set the width of the dropdown
                            this.eGui.style.width = '140px'; // Adjust the width as needed

                            this.eGui.addEventListener('change', (event) => {{
                                this.params.setValue(event.target.value);
                            }});
                        }}

                        getGui() {{
                            return this.eGui;
                        }}
                    }}
    """)

                
                
                st.markdown("""
                    <style>
                        .stExpander, .stContainer {
                        margin-bottom: 0px; /* Adjust bottom margin to create space between widgets */
                    }
                        .stExpander, .stContainer {
                        padding: 0px; /* Optional: Add padding inside the widget */
                    }
                    </style>
                    """, unsafe_allow_html=True)

                # Configure GridOptions for the main grid
                gb = GridOptionsBuilder.from_dataframe(Trans_df)

                # List of columns to hide
                book_columns = [
                            "Booking Date",
                            "Booked on",
                            "Booking status",
                            "Booked By",
                            "DoctorName",
                            "Consultation Date",
                            "Received Date",
                            "Received By",
                            "Received Status",
                            "Received Comments",
                            "Dispensed By",
                            "Collection status",
                            "Collection Date",
                            "Dispatched Date",
                            "Dispatched By",
                            "Month",
                            "Transaction Type",
                            "Year",
                           "Modified",
                            "Modified By",
                            "Level",
                            "Unique Id",
                            "Item Type",
                            "Property Bag",
                            "ID",
                            "Cycle",
                            "owshiddenversion",
                            "Created",
                            "Title",
                            "Name",
                            "Effective Permissions Mask",
                            "ScopeId",
                            "URL Path",
                            "Approval Status",
                            "mobile",
                            "MVC", 
                            "Collection Comments"
                ]
            
                # Hide specified columns
                for col in book_columns:
                    gb.configure_column(field=col, hide=True, pinned='right')

                # Configure non-editable columns
                non_editable_columns = [
                        "Title",
                        "UHID",
                        "Patientname",
                        "mobile",
                        "Cycle",
                        "DoctorName",
                        "Dispatched Date",
                        "Received Comments"
                        
                ]
                for column in non_editable_columns:
                    gb.configure_column(column, editable=False,filter=True)

                # Configure specific columns with additional settings
                gb.configure_column('Dispatched status', editable=False, cellRenderer=checkbox_renderer, pinned='right', minWidth=50)
                gb.configure_selection(selection_mode='single')
                gb.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
                gb.configure_column('UHID', editable=False,filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
                gb.configure_column('Location', cellEditor='agSelectCellEditor', cellEditorParams={'values': unique_item_descriptions}, cellRenderer=dropdown_renderer, cellStyle={'width': '300px'} )
                gb.configure_column("Dispatched Date", editable=False, cellRenderer=date_renderer)
    
                # Configure the default column to be editable
                gb.configure_default_column(editable=True, minWidth=150, flex=0)

                # Build the grid options
                gridoptions = gb.build()
                
                
                #Add manual selection configuration
                gridoptions.update({
                    'rowSelection': 'single',
                    'onSelectionChanged': JsCode("""
                        function onSelectionChanged(event) {
                            const selectedRows = event.api.getSelectedRows();
                            const selectedPatient = selectedRows.length > 0 ? selectedRows[0].Patientname : null;
                            window.parent.postMessage({ type: 'SELECT_PATIENT', patient: selectedPatient }, '*');
                        }
                    """)
                })

                # Streamlit app

                with st.form('Dispatch') as f:
                    with card_container(key="Billorder"):
                        # Display the AgGrid table
                        response = AgGrid(
                            Trans_df,
                            gridOptions=gridoptions,
                            editable=True,
                            allow_unsafe_jscode=True,
                            theme='balham',
                            height=120,
                            fit_columns_on_grid_load=True
                        )
                        
                        
                        cols = st.columns(6)
                        with cols[5]:
                            st.form_submit_button(" Confirm", type="primary")
                            
                
                selected_row = response['selected_rows']
                
                Selecetd_dataframe=pd.DataFrame(selected_row)
                
                rowcount=len(Selecetd_dataframe)
                
                #st.write(Selecetd_dataframe)
                
                # Initialize session state if not already done
                if 'Patient_name' not in st.session_state:
                    st.session_state.Patient_name = ''
                                
                if rowcount > 0:
                    try:
                        patient_name = Selecetd_dataframe.iloc[0]['Patientname']
                        st.session_state.Patient_name = patient_name
                        #st.write(st.session_state.Patient_name)
                    except IndexError:
                        pass  # Suppress IndexError silently
                    except KeyError:
                        pass  # Suppress KeyError silently
                                
                    #st.write(Patient_name)
                    #st.write("Selected Row:", selected_row)
                #else:
                    #st.write("No row selected")
                
                                
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

                # Handle child grid display using Streamlit components
                selected_category = st.session_state.Patient_name
                    
                if selected_category:
                            #st.write(f"Prescription for: {selected_category}")
                            with card_container(key="Billpre" f"Prescription for: {selected_category}"):
                                filtered_child_data = Details_df[Details_df['Patientname'] == selected_category]
                                
                                gd = GridOptionsBuilder.from_dataframe(filtered_child_data)
                                
                                # List of columns to hide
                                details_columns = [
                                    "mobile", "Company Type", "RateContract", "Speciality",    
                                    "DoctorName", "Location", "Medical Centre", "TeleDoctor",
                                    "Facility", "UHID", "Patientname","S.No"
                                ]
                                
                                # Hide specified columns
                                for col in details_columns:
                                    gd.configure_column(field=col, hide=True, pinned='right')
                                    
                                    
                                @st.cache_data
                                def get_unique_item_descriptions():
                                    return chronic_df['Drugs'].unique().tolist()

                                # Fetch unique item descriptions
                                unique_item_descriptions = get_unique_item_descriptions()
                                
                                
                                
                                # Define dropdown options for specified columns
                                dropdown_options = {
                                    'Itemname': unique_item_descriptions
                            }    
                                
                                for col, options in dropdown_options.items():
                                    gd.configure_column(field=col, cellEditor='agSelectCellEditor', cellEditorParams={'values': options})

                                
                                # Configure editable columns
                                editable_columns = ["Itemname", "Quantity"]
                                for column in editable_columns:
                                    gd.configure_column(column, editable=True)
                                    
                                
                                # Configure the default column to be editable
                                gd.configure_default_column(editable=True,minWidth=100, flex=0)    
                                    
                                
                                # Configure the default column to be editable
                                gd.configure_default_column(editable=True, minWidth=150, flex=0)

                                # Build the grid options
                                gridoptions = gd.build()

                
                with card_container(key="disp"):
                    
                    try:
                        
                        # Fetch the data from the AgGrid Table
                        res = response['data']
                        #st.table(res)
                        
                        df = pd.DataFrame(res)
                
                        # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                        pres_df = df[df['Dispatched status'] == 'Dispatched']
                        
                        # Convert 'Consultation Date' to datetime
                        pres_df['Dispatched Date'] = pd.to_datetime(pres_df['Dispatched Date'], errors='coerce')

                        # Fill NaN values with the formatted date
                        pres_df['Dispatched Date'] = pres_df['Dispatched Date'].fillna(formatted_date)
                        
                        # Convert 'Consultation Date' to string in 'YYYY-MM-DD' format
                        pres_df['Dispatched Date'] = pres_df['Dispatched Date'].dt.strftime('%d/%m/%Y')
                        
                        pres_df=pres_df[[
                                        "ID",
                                        "Title",
                                        "UHID",
                                        "Patientname",
                                        "Location",
                                        "Dispatched status",
                                        "Dispatched Date",
                                        "Dispatched By",
                                        "Month",
                                        "Year",
                                        "Transaction Type","Cycle"]]
        
                        
                        # Display the filtered DataFrame
                        #st.dataframe(Appointment_df)
                        
                        with card_container(key="billdsis2"):
                            cols = st.columns(1)
                            with cols[0]:
                                with card_container(key="bil1dis3"):
                                    ui.table(data=pres_df, maxHeight=300)
                    
                    
                    except Exception as e:
                        st.error(f"Failed to update to SharePoint: {str(e)}")
                        st.stop() 
                    
                    
                    def submit_to_sharepoint(Appointment_df):
                        try:
                            with st.spinner('Submitting...'):
                                sp = SharePoint()
                                site = sp.auth()
                                target_list = site.List(list_name='Home Delivery')

                                # Iterate over the DataFrame and update items in the SharePoint list
                                for ind in pres_df.index:
                                    item_id = pres_df.at[ind, 'ID']
                                    Dispatch_status = pres_df.at[ind, 'Dispatched status']
                                    Dispatch_date = pres_df.at[ind, 'Dispatched Date']
                                    Dispatch_by = pres_df.at[ind, 'Dispatched By']
                                    Location = pres_df.at[ind, 'Location']
                                    Transaction_by = pres_df.at[ind, 'Transaction Type']

                                    item_creation_info = {
                                        'ID': item_id, 
                                        'Dispatched status':Dispatch_status,
                                        'Dispatched Date': Dispatch_date,
                                        'Dispatched Date': Dispatch_date,
                                        'Transaction Type': Transaction_by,
                                        'Dispatched By':Dispatch_by,
                                        'Location': Location
                                        
                                    }

                                    logging.info(f"Updating item ID {item_id}: {item_creation_info}")

                                    response = target_list.UpdateListItems(data=[item_creation_info], kind='Update')
                                    logging.info(f"Response for index {ind}: {response}")

                            st.success("Succefully submitted", icon="✅")
                        except Exception as e:
                            logging.error(f"Failed to update to SharePoint: {str(e)}", exc_info=True)
                            st.error(f"Failed to update to SharePoint: {str(e)}")
                            st.stop()

                    cols = st.columns(4)

                    with cols[2]:
                    # Button to submit DataFrame to SharePoint
                        ui_but = ui.button("Submit ", key="subbtn")
                        if ui_but:
                            submit_to_sharepoint(pres_df)   
                            
                    with cols[2]:
                        ui_result = ui.button("Refresh", key="btn")  
                        if ui_result: 
                            with st.spinner('Wait! Reloading view...'):  
                                    st.cache_data.clear()
                                    AllTrans_df = load_new() 
                            
            
       

if __name__ == "__main__":
    app()