import streamlit as st
import pandas as pd
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import List
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
        raise Exception(f"Failed to authenticate: {ctx_auth.get_last_error()}")

def upload_to_sharepoint(df, ctx):
    try:
        # Get the SharePoint list
        target_list = ctx.web.lists.get_by_title(list_name)
        ctx.load(target_list)
        ctx.execute_query()

        # Insert rows into the SharePoint list
        for index, row in df.iterrows():
            item_creation_info = row.to_dict()

            # Ensure the values are strings and handle empty values
            for key, value in item_creation_info.items():
                if value is None or pd.isna(value):
                    item_creation_info[key] = ""
                else:
                    item_creation_info[key] = str(value)

            # Add item to SharePoint list
            target_list.add_item(item_creation_info).execute_query()
            st.write(f"Inserted row {index + 1} into SharePoint.")

        st.success("All rows have been inserted successfully.")
    except Exception as e:
        st.error(f"Failed to upload to SharePoint: {str(e)}")

def app():
    st.title("Upload Excel File to SharePoint")
    
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
        st.write(f"""<span style="color:red;">
                    You are not Logged in, click account to Log in/Sign up to proceed.
                </span>""", unsafe_allow_html=True)
        
    if st.session_state.is_authenticated:
        location=st.session_state.Region
        staffnumber=st.session_state.staffnumber
        department = st.session_state.Department
        
        
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
    
        

    # Upload Excel file widget
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

    # If a file is uploaded
    if uploaded_file is not None:
        Trans_df = pd.read_excel(uploaded_file)
        
        # Convert date columns to the required format
        date_columns = ['BookingDate', 'ConsultationDate', 'DispatchedDate', 'ReceivedDate', 'CollectionDate', 'Booked on']
        available_date_columns = [col for col in date_columns if col in df.columns]
        
        for column in available_date_columns:
            df[column] = pd.to_datetime(df[column]).dt.strftime('%d/%m/%Y')

        # Replace NaN values with blank strings and convert columns to strings
        df = df.fillna('').astype(str)

        # Display the DataFrame to the user
        st.write("Uploaded Data Preview:")
        st.dataframe(Trans_df)
        
         
        Trans_df['Dispatched Date'] = Trans_df['Dispatched Date'].fillna(formatted_date)
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
                    "BookingDate",
                    "Bookedon",
                    "Bookingstatus",
                    "BookedBy",
                    "DoctorName",
                    "ConsultationDate",
                    "ReceivedDate",
                    "ReceivedBy",
                    "ReceivedStatus",
                    "ReceivedComments",
                    "DispensedBy",
                    "Collectionstatus",
                    "CollectionDate",
                    "DispatchedDate",
                    "DispatchedBy",
                    "Month",
                    "TransactionType",
                    "Year",
                    "Cycle",
                    "Modified",
                    "ModifiedBy",
                    "Level",
                    "Unique Id",
                    "ItemT ype",
                    "Property Bag",
                    "ID",
                    "Cycle",
                    "owshidden version",
                    "Created",
                    "Title",
                    "Name",
                    "Effective Permissions Mask",
                    "Scope Id",
                    "URL Path",
                    "Approval Status",
                    "mobile",
                    "MVC", 
                    "CollectionComments"
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
            st.header('Dispatch  Package🔖')
            
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
                    
    

        # Submit button to trigger the upload to SharePoint
        if st.button("Submit to SharePoint"):
            ctx = connect_to_sharepoint()
            upload_to_sharepoint(df, ctx)
    else:
        st.write("Please upload an Excel file to proceed.")

if __name__ == "__main__":
    app()
