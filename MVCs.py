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
        
        @st.cache_data(ttl=80, max_entries=2000, show_spinner=False, persist=False, experimental_allow_widgets=False)
        def load_new():
            columns = [
                "Title", "ID", "UHID", "Patientname", "mobile", "Location", "Booking status", 
                "Booking Date", "Booked on", "Booked By", "DoctorName", "Consultation Status", 
                "Consultation Date", "Dispatched status", "Dispatched Date", "Dispatched By", 
                "Received Date", "Received By","Received Comments", "Received Status", "Dispensed By", "Collection status", 
                "Collection Date", "MVC", "Cycle", "Collection Comments", "Month", 
                "Transaction Type", "Year","Corrected"
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
        
        current_date = datetime.now().date()
        # Format the date as a string (e.g., YYYY-MM-DD)
        formatted_date = current_date.strftime("%d/%m/%Y")
        
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
                    (AllTrans_df['Location'] == location) & 
                    (~AllTrans_df['Collection status'].isnull())]
            
            
            Trans_df['MVC check'] = Trans_df.apply(
                lambda row: 'Not Valid/Duplicate' if Trans_df['MVC'].duplicated(keep=False)[row.name]
                else ('Valid' if len(str(row['MVC'])) == 13 else 'Not Valid'),
                axis=1)
            
            #st.write(staffname)
            names_list = [
                "Full",
                "Partial"
    
            ]
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
                                params.setValue('True');
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
                        this.eGui.checked = params.value === 'True';
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
            
            textarea_renderer = JsCode("""
                class TextareaRenderer {
                    init(params) {
                        this.params = params;
                        this.eGui = document.createElement('textarea');
                        
                        // Set the width and height of the textarea
                        this.eGui.style.width = '150px'; // Adjust the width as needed
                        this.eGui.style.height = '20px'; // Adjust the height as needed

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
            
            
            textarea_renderer2 = JsCode("""
                    class SingleLineTextRenderer {
                        init(params) {
                            this.params = params;
                            this.eGui = document.createElement('input');
                            this.eGui.type = 'text'; // Set the input type to text for single-line input

                            // Set the width of the input
                            this.eGui.style.width = '150px'; // Adjust the width as needed
                            this.eGui.style.height = '20px'; // Adjust the height as needed

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
            
            
            dropdown_renderer = JsCode(f"""
                class DropdownRenderer {{
                    init(params) {{
                        this.params = params;
                        this.eGui = document.createElement('select');

                        // Set the width and height of the dropdown
                        this.eGui.style.width = '150px'; // Adjust the width as needed
                        this.eGui.style.height = '20px'; // Adjust the height as needed

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
                        "ID",
                        "Title",
                        "mobile",
                        "Booking status",
                        "Booking Date",
                        "Booked on",
                        "Booked By",
                        "DoctorName",
                        "Designation",
                        "Staffnumber",
                        "Staffname",
                        "Consultation Status",
                        "Received Status",
                        "Consultation Date",
                        "Dispatched status",
                        "Dispatched Date",
                        "Dispatched By",
                        "Received Comments",
                        "Collection Comments",
                        "Cycle",
                        "Received Date",
                        "Dispensed  By",
                        "Received By",
                        "Dispensed By",
                        "Month",
                        "Corrected",
                        "Transaction Type",
                        "Year"
                
            ]           
           
            # Hide specified columns
            for col in book_columns:
                gb.configure_column(field=col, hide=True, pinned='right',filter=True)
                
            

            # Configure non-editable columns
            non_editable_columns = [
                    "UHID",
                    "Patientname",
                    "Location",
                    "Collection status",
                    "Collection Date"
                    
                  
                    
            ]
            for column in non_editable_columns:
                gb.configure_column(column, editable=False)
                
            
            
            gb.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('UHID', editable=False,filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('MVC', editable=False, cellRenderer=textarea_renderer2, minWidth=50)
            
            # Configure the default column to be editable
            gb.configure_default_column(editable=True, minWidth=150, flex=0)
            
             # Build the grid options
            gridoptions = gb.build()
            
            
            gridoptions['columnDefs'].append({"field": "Corrected","headerName": "Corrected", "cellRenderer": checkbox_renderer,"editable": False})

            
            
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
            # Streamlit container to act as card
            with st.form('colle2') as f:
                st.header('Edit  MVCs🔖')
               
                with card_container(key="collect2"):
                    # Display the AgGrid table
                    response = AgGrid(
                        Trans_df,
                        gridOptions=gridoptions,
                        editable=True,
                        allow_unsafe_jscode=True,
                        theme='balham',
                        height=300,
                        fit_columns_on_grid_load=True
                    )
                    
                    cols = st.columns(6)
                    with cols[5]:
                        st.form_submit_button(" Confirm ", type="primary")  
                
                    
            with card_container(key="colecnew"):
                
                try:
                    
                    # Fetch the data from the AgGrid Table
                    res = response['data']
                    #st.table(res)
                    
                    df = pd.DataFrame(res)
            
                    # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                    pres_df = df[df['Corrected'].isin(['True'])]
                    
                   
                    
                    
                    pres_df=pres_df[[
                                    "ID",
                                    "Title",
                                    "UHID",
                                    "Patientname",
                                    "Location",
                                    "Collection status",
                                    "Collection Date",
                                    "Dispensed By",
                                    "MVC",
                                    "Corrected"]]

                    # Display the filtered DataFrame
                    #st.dataframe(Appointment_df)
                    
                    with card_container(key="colec4"):
                        cols = st.columns(1)
                        with cols[0]:
                            with card_container(key="collec5"):
                                ui.table(data=pres_df, maxHeight=300)
                
                
                except Exception as e:
                    st.error(f"Failed to update to SharePoint: {str(e)}")
                    st.stop() 
                
                
                def validate_appointment_data(df):
                    """
                    Validate the DataFrame to check for 'MVC' fields that are not 13 digits long.
                    Returns a boolean indicating if the data is valid and a list of row indices with issues.
                    """
                    # Find rows where 'MVC' is not 13 digits long
                    invalid_rows = df[df['MVC'].apply(lambda x: len(str(x)) != 13)].index.tolist()
                    
                    # If there are any invalid rows, return False and the list of invalid row indices
                    if invalid_rows:
                        return False, invalid_rows
                    
                    # If all rows are valid, return True and an empty list
                    return True, []


                def submit_to_sharepoint(Appointment_df):
                    # Validate data before submission
                    is_valid, invalid_rows = validate_appointment_data(Appointment_df)
                    
                    if not is_valid:
                        st.error(f"MVC is invalid: {invalid_rows}")
                        return
                    try:
                        with st.spinner('Submitting...'):
                            sp = SharePoint()
                            site = sp.auth()
                            target_list = site.List(list_name='Home Delivery')

                            # Iterate over the DataFrame and update items in the SharePoint list
                            for ind in pres_df.index:
                                item_id = pres_df.at[ind, 'ID']
                                collection_date = pres_df.at[ind, 'Collection Date']
                                MVC_by = pres_df.at[ind, 'MVC']   


                                item_creation_info = {
                                    'ID': item_id,
                                    'Collection Date': collection_date,
                                    'MVC':MVC_by
                                }

                                logging.info(f"Updating item ID {item_id}: {item_creation_info}")

                                response = target_list.UpdateListItems(data=[item_creation_info], kind='Update')
                                logging.info(f"Response for index {ind}: {response}")

                            st.success("Sucessfully submitted", icon="✅")
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
    else:
        st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")