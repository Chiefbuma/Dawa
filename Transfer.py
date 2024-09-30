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
            
            #st.write(mainall)
            
            #num_rows = mainall.shape[0]

            # Display the number of rows
            #st.write(f"The number of rows in the DataFrame is: {num_rows}")
                        
            # Ensure the 'Cycle' column is numeric (if it's not already)
            mainall['Cycle'] = pd.to_numeric(mainall['Cycle'], errors='coerce')

            response = supabase.from_('usersD').select('*').eq('staffnumber', staffnumber).execute()
            usersD_df = pd.DataFrame(response.data)
            
            staffname = usersD_df['staffname'].iloc[0]

            current_date = datetime.now().date()
            
            formatted_date = current_date.strftime("%d/%m/%Y")
            
            # Get a list of unique values in the 'Cycle' column
            Cycle = mainall['Cycle'].unique().tolist()
            
            with card_container(key="receive3"):
                cols = st.columns([4,1])
                with cols[0]:
                    st.header('Transfer in/Return Package🔖')
                with cols[1]:
                    with st.container():
                        choice = st.selectbox('Select Cycle', Cycle) 
                        if choice : 
                            AllTrans_df=mainall[mainall['Cycle'] == choice]
                                
             
            
            selected_option = ui.tabs(options=['Transfer In','Transfer Out'], default_value='Transfer Out', key="kanaries")
           
            if selected_option=="Transfer Out":

                Trans_df = AllTrans_df[ 
                    (AllTrans_df['Dispatched status']=="Dispatched") &
                    (AllTrans_df['Location'] == location) ]
                #st.write(Trans_df)
            
                Trans_df['Transfer From']= location
                
                Trans_df['Transfer Date'] = Trans_df['Received Date'].fillna(formatted_date)
            
                Trans_df['Transferred By']=staffname
                
               
            else :
        
                Trans_df = AllTrans_df[ 
                        (AllTrans_df['Dispatched status']=="Dispatched") &
                        (AllTrans_df['Transfer To']==location) &
                        (AllTrans_df['Location']!=location)]
               
                Trans_df['Received Date'] = Trans_df['Received Date'].fillna(formatted_date)
            
                Trans_df['Received By']=staffname
                
                Trans_df['Received Status']= "Pending"
                        
                 
            
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
                            params.setValue('Received');
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
                    this.eGui.checked = params.value === 'Received';
                }
            }
            """)
            
            
            # JavaScript for checkbox renderer
            checkbox_renderer2 = JsCode("""
            class CheckboxRenderer {
                init(params) {
                    this.params = params;
                    this.eGui = document.createElement('input');
                    this.eGui.setAttribute('type', 'checkbox');
                    
                    // Default the checkbox to unchecked
                    this.eGui.checked = params.value === '';
                    
                    this.eGui.addEventListener('click', (event) => {
                        if (event.target.checked) {
                            params.setValue('Transferred');
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
                    this.eGui.checked = params.value === 'Transferred';
                }
            }
            """)
            
            textarea_renderer = JsCode("""
                class TextareaRenderer {
                    init(params) {
                        this.params = params;
                        this.eGui = document.createElement('textarea');
                        
                        // Set the width and height of the textarea
                        this.eGui.style.width = '120px'; // Adjust the width as needed
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
                   
            if selected_option == "Transfer In":
                

                Trans_df['Transfer To']= location
                Trans_df['Location']= location
                Trans_df['Transaction Type']= "Transfer In"
                Trans_df['Received Date']= Trans_df['Received Date'].fillna(formatted_date)
                
                
                gb = GridOptionsBuilder.from_dataframe(Trans_df)
                
                gb.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
                gb.configure_column('UHID', editable=False,filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
                gb.configure_column('Transfer From', editable=False)
                gb.configure_column('Transfer Comments', editable=False, cellRenderer=textarea_renderer,width=10)
                gb.configure_column('Transfer To', editable=False)
                gb.configure_column('Received Status', editable=False, cellRenderer=checkbox_renderer, pinned='right', minWidth=50)
                # List of columns to hide
                book_columns = [
                            "Booking Date",
                            "Booked on",
                            "Booking status",
                            "Booked By",
                            "Location",
                            "Transfer Status",
                            "DoctorName",
                            "Consultation Status",
                            "Collection status",
                            "Collection Date",
                            "Dispatched Date",
                            "Dispensed By",
                            "Dispatched By",
                            "Consultation Date",
                            "Received Date",
                            "Transferred By",
                            "Received Comments",
                            "Received By",
                            "Month",
                            "Transfer Date",
                            "Transaction Type",
                            "Year",
                            "Modified",
                            "Modified By",
                            "Level",
                            "Unique Id",
                            "Item Type",
                            "Property Bag",
                            "MVC",
                            "Collection Comments",
                            "owshiddenversion",
                            "Created",
                            "Title",
                            "Name",
                            "Effective Permissions Mask",
                            "ScopeId",
                            "URL Path",
                            "Cycle",
                            "Approval Status",
                            "mobile" ]
                    
            elif selected_option == "Transfer Out":
                    
                    Trans_df['Transaction Type']= "Transfer Out"
                
                    Trans_df['Transfer From']= location
                    
                    # List of columns to hide
                    book_columns = [
                            "Booking Date",
                            "Booked on",
                            "Booking status",
                            "Booked By",
                            "DoctorName",
                            "Consultation Status",
                            "Collection status",
                            "Collection Date",
                            "Dispatched Date",
                            "Dispensed By",
                            "Dispatched By",
                            "Consultation Date",
                            "Received Date",
                            "Received Status",
                            "Transferred By",
                            "Received Comments",
                            "Received By",
                            "Month",
                            "Transfer Date",
                            "Transaction Type",
                            "Location",
                            "Year",
                            "Modified",
                            "Modified By",
                            "Level",
                            "Unique Id",
                            "Item Type",
                            "Property Bag",
                            "ID",
                            "MVC",
                            "Collection Comments",
                            "owshiddenversion",
                            "Created",
                            "Title",
                            "Cycle",
                            "Name",
                            "Effective Permissions Mask",
                            "ScopeId",
                            "URL Path",
                            "Approval Status",
                            "mobile",
                            "Accept"]
                    
                    
                    gb = GridOptionsBuilder.from_dataframe(Trans_df)
                    gb.configure_column('Patientname', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
                    gb.configure_column('UHID', editable=False,filter="agTextColumnFilter", filter_params={"filterOptions": ["contains", "notContains", "startsWith", "endsWith"]})
                    gb.configure_column('Transfer Comments', editable=False, cellRenderer=textarea_renderer,width=10)
                    gb.configure_column('Transfer From', editable=False)
                    gb.configure_column('Transfer To', cellEditor='agSelectCellEditor', cellEditorParams={'values': unique_item_descriptions}, cellRenderer=dropdown_renderer, cellStyle={'width': '300px'} )
                    gb.configure_column('Transfer Status', editable=False, cellRenderer=checkbox_renderer2, pinned='right', minWidth=50)
            
            
            with st.form('Transfer') as f:
                st.header('Transfer/Return  Package🔖')

                # Hide specified columns
                for col in book_columns:
                    gb.configure_column(field=col, hide=True,filter=True)

                # Configure non-editable columns
                non_editable_columns = [
                        "Title",
                        "UHID",
                        "Patientname",
                        "mobile",
                        "Cycle"
                   
                    
                        
                ]
                for column in non_editable_columns:
                    gb.configure_column(column, editable=False)

                # Configure specific columns with additional settings
            
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

                with card_container(key="transfernew"):
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
                    st.form_submit_button("Confirm", type="primary")  
            
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

                
        with card_container(key="reveived" f"CONFIRM TRANSFER"):
            try:
                
                # Fetch the data from the AgGrid Table
                res = response['data']
                #st.table(res)
                
                df = pd.DataFrame(res)
                
                # Filter the DataFrame to include only rows where "Booking status" is "Booked"
                
                
                if selected_option == "Transfer In":
                    
                    pres_df = df[(df['Received Status'] == 'Received')]
                    pres_df=pres_df[[
                                "id",
                                "UHID",
                                "Patientname",
                                "Transfer To",
                                "Transfer From",
                                "Received Status",
                                "Received Date",
                                "Location",
                                "Received By",
                                "Transferred By",
                                "Transfer Date",
                                "Transfer Comments",
                                "Month",
                                "Year",
                                "Transaction Type",
                                "Cycle"]]
                else:
                    
                    pres_df = df[df['Transfer Status'] == 'Transferred']
                    
                    pres_df=pres_df[[
                                "id",
                                "UHID",
                                "Patientname",
                                "Transfer From",
                                "Transfer To",
                                "Transferred By",
                                "Transfer Date",
                                "Transfer Comments",
                                "Transfer Status",
                                "Month",
                                "Year",
                                "Transaction Type",
                                "Cycle"]]

                
                # Display the filtered DataFrame
                #st.dataframe(Appointment_df)
                
                with card_container(key="billds2"):
                    cols = st.columns(1)
                    with cols[0]:
                        with card_container(key="bil1d3"):
                            ui.table(data=pres_df, maxHeight=300)
            
            except Exception as e:
                st.error(f"Failed to update databse: {str(e)}")
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
