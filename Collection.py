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

            Allresponse = supabase.from_('Home_Delivery').select('*').execute()
            
            mainall = pd.DataFrame(Allresponse.data)
            
            response = supabase.from_('usersD').select('*').eq('staffnumber', staffnumber).execute()
            usersD_df = pd.DataFrame(response.data)
            
            staffname = usersD_df['staffname'].iloc[0]
            
            # Get a list of unique values in the 'Cycle' column
            Cycle = mainall['Cycle'].unique().tolist()
            
            with card_container(key="collect3"):
                cols = st.columns([4,1])
                with cols[0]:
                    st.header('Collect  Package🔖')
                with cols[1]:
                    with st.container():
                        choice = st.selectbox('Select Cycle', Cycle) 
                        if choice : 
                            AllTrans_df=mainall[mainall['Cycle'] == choice]
                                
                            if department=="Admin":
                                Trans_df = AllTrans_df[
                                        (AllTrans_df['Received Status'] == 'Received') &
                                        (AllTrans_df['Transaction Type']=='Receipt')]
                            else:   
                                Trans_df = AllTrans_df[
                                        (AllTrans_df['Received Status'] == 'Received') & 
                                        (AllTrans_df['Location'] == location) & 
                                        (AllTrans_df['Transaction Type']=='Receipt')]
                
             #st.write(Trans_df)
            current_date = datetime.now().date()
            formatted_date = current_date.strftime("%d/%m/%Y")
                    
            Trans_df['Dispensed By']=staffname
            
            Trans_df['Transaction Type']= "Collection"
            
        
            
            
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
                                params.setValue('Collected');
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
                        this.eGui.checked = params.value === 'Collected';
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
                            this.eGui.style.width = '200px'; // Adjust the width as needed
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
                        "id",
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
                        "Consultation Date",
                        "Dispatched status",
                        "Dispatched Date",
                        "Dispatched By",
                        "Received Comments",
                        "Received Date",
                        "Dispensed  By",
                        "Transfer To",
                        "Transferred By",
                        "Transfer Date",
                        "Transfer Status",
                        "Transfer From",
                        "Transfer Comments",
                        "Received By",
                        "Dispensed By",
                        "Month",
                        "Transaction Type",
                        "Year"
                
            ]           
        
            # Hide specified columns
            for col in book_columns:
                gb.configure_column(field=col, hide=True, pinned='right',filter=True)

            # Configure non-editable columns
            non_editable_columns = [
        
                    "Received Status",
                    "Month",
                    "Dispensed By",
                    "Year"
        
            ]
            for column in non_editable_columns:
                gb.configure_column(column, editable=False)
                
            
        
            gb.configure_column('UHID', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('Location', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('Collection status', cellEditor='agSelectCellEditor', cellEditorParams={'values': names_list}, cellRenderer=dropdown_renderer)
            gb.configure_column("Collection Date", editable=False, cellRenderer=date_renderer)
            gb.configure_column('MVC', editable=True, cellRenderer=textarea_renderer2, pinned='right', minWidth=50)
            gb.configure_column('Cycle', editable=False,filter="agTextColumnFilter",minWidth=5, filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
            gb.configure_column('Collection Comments', editable=True, cellRenderer=textarea_renderer2, minWidth=100)
            
            # Configure the default column to be editable
            gb.configure_default_column(editable=True, minWidth=150, flex=0)

            # Build the gri
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

            # Streamlit container to act as card
        with st.form('colle2') as f:
            
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
                
                # Form submission logic with validation
                cols = st.columns(6)
                with cols[5]:
                    # Form submit button
                     st.form_submit_button("Confirm", type="primary")
                    
        with card_container(key="colecnew"):
            
            try:
                
                # Fetch the data from the AgGrid Table
                res = response['data']
                #st.table(res)
                
                df = pd.DataFrame(res)
        
                # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                pres_df = df[df['Collection status'].isin(['Full','Partial','Returned',''])]
                
                
                        
                pres_df=pres_df[[
                                "id",
                                "UHID",
                                "Patientname",
                                "Location",
                                "Collection status",
                                "Collection Date",
                                "Dispensed By",
                                "MVC",
                                "Collection Comments"]]

                
                # Display the filtered DataFrame
                #st.dataframe(Appointment_df)
                
                with card_container(key="colec4"):
                    cols = st.columns(1)
                    with cols[0]:
                        with card_container(key="collec5"):
                            ui.table(data=pres_df, maxHeight=300)
            
            
            except Exception as e:
                st.error(f"Failed to update : {str(e)}")
                st.stop() 
            
            
            # Function to update Supabase table
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

                        st.success(f"Successfully updated record ID {record_id}")

                except Exception as e:
                    st.error(f"Failed to update Supabase: {str(e)}")
                    st.stop()

            try:
                # Fetch the data from Supabase table "Home_Delivery"
                response = supabase.table("Home_Delivery").select("*").execute()

            except Exception as e:
                st.error(f"Failed to fetch or process data: {str(e)}")
                st.stop()

            # Action buttons to submit or refresh data
            cols = st.columns(4)
            with cols[2]:
                ui_but = ui.button("Submit", key="subbtn")
                if ui_but:
                    if (pres_df == 'None').any().any():
                        st.error("Please fill in all required fields (MVC and Collected Date) before confirming.")
                    else:
                        with st.spinner('Wait! Reloading view...'):
                            # Call the function to update Supabase with the filtered data
                            update_supabase_table(pres_df, table_name="Home_Delivery", id_column="id")

            with cols[2]:
                ui_result = ui.button("Refresh", key="btn")
                if ui_result:
                    with st.spinner('Wait! Reloading view...'):
                        st.cache_data.clear()
   
    else:
        st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")
