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
        
        
        #AllTrans_df = load_data(email_user, password_user, sharepoint_url, list_name)
        @st.cache_data(ttl=80, max_entries=2000, show_spinner=False, persist=False, experimental_allow_widgets=False)
        def load_new():
            columns = [
                "Title", "ID", "UHID", "Patientname", "mobile", "Location", "Booking status", 
                "Booking Date", "Booked on", "Booked By", "DoctorName", "Consultation Status", 
                "Consultation Date", "Dispatched status", "Dispatched Date", "Dispatched By", 
                "Received Date", "Received By", "Received Status", "Dispensed By", "Collection status", 
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

        AllTrans_df = load_new()

        #st.write(AllTrans_df)
        
        #st.write(AllTrans_df)
        current_date = datetime.today().date()
        
        # Format the date as a string (e.g., YYYY-MM-DD)
        formatted_date = current_date.strftime("%d/%m/%Y")
       
        #st.write(formatted_date)
        
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
            
            
            response = supabase.from_('StaffList').select('*').eq('StaffNumber', staffnumber).execute()
            usersD_df = pd.DataFrame(response.data)
            
            staffname = usersD_df['StaffName'].iloc[0]
            
            #st.write(staffname)
            
            Trans_df = AllTrans_df[
                (AllTrans_df['DoctorName'] == staffname) &
                (AllTrans_df['Booking status'] == 'Booked') &  
                (AllTrans_df['Consultation Status']=='Pending')]
                
            
            #st.write(Trans_df)
            Trans_df['DoctorName']=staffname
                
           # Convert 'Consultation Date' to datetime
            Trans_df['Consultation Date'] = pd.to_datetime(Trans_df['Consultation Date'], errors='coerce')

            # Fill NaN values with the formatted date
            Trans_df['Consultation Date'] = Trans_df['Consultation Date'].fillna(formatted_date)

            # Convert 'Consultation Date' to string in 'YYYY-MM-DD' format
            Trans_df['Consultation Date'] = Trans_df['Consultation Date'].dt.strftime('%d/%m/%Y')
            
            # Convert 'Consultation Date' to string in 'YYYY-MM-DD' format
            Trans_df['Transaction Type']="Consult"
            #st.write(staffname)
            
            #st.write(Trans_df)
            
            #st.write(formatted_date)
            
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
                            params.setValue('Consulted');
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
                    this.eGui.checked = params.value === 'Consulted';
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
                    margin-bottom: 100px; /* Adjust bottom margin to create space between widgets */
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
                        "Booked By",
                        "Collection Comments",
                        "Dispatched status",
                        "Dispatched Date",
                        "Dispatched By",
                        "Collection status",
                        "Consultation Date",
                        "Collection Date",
                        "Received Date",
                        "Received By",
                        "Received Status",
                        "Dispensed By",
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
                        "owshiddenversion",
                        "Created",
                        "Title",
                        "Name",
                        "Effective Permissions Mask",
                        "ScopeId",
                        "URL Path",
                        "Approval Status",
                        "mobile",
                        "Cycle",
                        "MVC",
                        "Collection "
                        

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
                    "Booking status",
                    "DoctorName",
                    "Consultation Date",
                     "Cycle"
                    

            ]
            
            for column in non_editable_columns:
                gb.configure_column(column, editable=False,filter=True)
        
             # Configure specific columns with additional settings
            gb.configure_column('Consultation Status', editable=False, cellRenderer=checkbox_renderer, pinned='right', minWidth=50)
            gb.configure_selection(selection_mode='single')
            gb.configure_column(
                field='Prescription',
                cellRenderer=cellRenderer_link,
                allow_unsafe_jscode=True
            )
            gb.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('UHID', editable=False,filter="agTextColumnFilter")
            # Configure the 'DoctorName' column with the dropdown renderer
            gb.configure_column('Location', cellEditor='agSelectCellEditor', cellEditorParams={'values': unique_item_descriptions}, cellRenderer=dropdown_renderer, cellStyle={'width': '300px'} )

            
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
            
            st.markdown(
                    """
                    <style>
                    .ag-theme-balham {
                        height: 30px; /* Set height for AgGrid container */
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
)
            with st.form('Bill') as f:
                st.header('Consult Patient🔖')
                    
                response = AgGrid(Trans_df,
                                gridOptions = gridoptions, 
                                editable=True,
                                allow_unsafe_jscode = True, 
                                theme = 'balham',
                                height = 120,
                                fit_columns_on_grid_load = True)

                    
                cols = st.columns(6)
                with cols[5]:
                    st.form_submit_button(" Confirm 🔒", type="primary")
    
                    
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

                            
                        with st.expander(f"VIEW PRESCRIPTION  FOR : {selected_category}",expanded=True):
                            # Inject custom CSS for solid border
                            response3 = AgGrid(
                                filtered_child_data,
                                gridOptions=gridoptions,
                                editable=True,
                                allow_unsafe_jscode=True,
                                theme='balham',
                                height=120,
                                fit_columns_on_grid_load=True
                            )
                                
                            try:
                                res3 = response3['data']
                                filtered_prescription = pd.DataFrame(res3)

                                def update_supabase_table(dataframe: pd.DataFrame, table_name: str, id_column: str):
                                    """
                                    Update Supabase table records using data from a DataFrame.

                                    Args:
                                    - dataframe: pd.DataFrame containing the data to update.
                                    - table_name: str, name of the Supabase table to update.
                                    - id_column: str, the column name in the DataFrame that contains unique IDs.
                                    """
                                    try:
                                        for index, row in dataframe.iterrows():
                                            # Convert the row to a dictionary
                                            record = row.to_dict()
                                            record_id = record.pop(id_column)
                                            
                                            # Update the Supabase table record
                                            response = supabase.table(table_name).update(record).eq(id_column, record_id).execute()
                                            if response.get('status') != 200:
                                                print(f"Failed to update record ID {record_id}: {response.get('error', 'Unknown error')}")
                                            else:
                                                print(f"Successfully updated record ID {record_id}")

                                    except Exception as e:
                                            st.error(f"Failed to update to SharePoint: {str(e)}")
                                            st.stop()

                            except Exception as e:
                                st.error(f"Failed to update to SharePoint: {str(e)}")
                                st.stop()
            
                    
            with card_container(key="Main12"):
                
                try:
                    
                    # Fetch the data from the AgGrid Table
                    res = response['data']
                    #st.table(res)
                    
                    df = pd.DataFrame(res)
            
                    # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                    pres_df = df[df['Consultation Status'] == 'Consulted']
                    
                    pres_df=pres_df[[
                                    "ID",
                                    "Title",
                                    "UHID",
                                    "Patientname",
                                    "Location",
                                    "Consultation Status",
                                    "Consultation Date",
                                    "DoctorName",
                                    "Month",
                                    "Year",
                                    "Transaction Type"]]
                    
                    cols = st.columns(1)
                    with cols[0]:
                        with card_container(key="bil1"):
                            ui.table(data=pres_df, maxHeight=300)
            
                
                except Exception as e:
                    st.error(f"Failed to update to SharePoint: {str(e)}")
                    st.stop() 
                
              
              
                def validate_appointment_data(df):
                    """
                    Validate the Appointment_df DataFrame to check for blank 'DoctorName' fields.
                    Returns a boolean indicating if the data is valid and a list of row indices with issues.
                    """
                    invalid_rows = df[df['Location']=="None"].index.tolist()
                    if invalid_rows:
                        return False, invalid_rows
                    return True, []

                def submit_to_sharepoint(Appointment_df):
                    # Validate data before submission
                    is_valid, invalid_rows = validate_appointment_data(Appointment_df)
                    
                    if not is_valid:
                        st.error(f"Location is blank in rows: {invalid_rows}")
                        return

                    try:
                        with st.spinner('Submitting...'):
                            sp = SharePoint()
                            site = sp.auth()
                            target_list = site.List(list_name='Home Delivery')

                            # Iterate over the DataFrame and update items in the SharePoint list
                            for ind in pres_df.index:
                                item_id = pres_df.at[ind, 'ID']
                                consultation_status = pres_df.at[ind, 'Consultation Status']
                                consultation_date = pres_df.at[ind, 'Consultation Date']
                                Location = pres_df.at[ind, 'Location']
                                

                                item_creation_info = {
                                    'ID': item_id, 
                                    'Consultation Status': consultation_status,
                                    'Consultation Date': consultation_date,
                                    'Location':Location
                                }

                                logging.info(f"Updating item ID {item_id}: {item_creation_info}")

                                response = target_list.UpdateListItems(data=[item_creation_info], kind='Update')
                                logging.info(f"Response for index {ind}: {response}")

                        st.success("succesfully submitted", icon="✅")
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
        
              
        else:
            st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")
