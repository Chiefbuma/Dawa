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
                    st.write(f"Inserted  {item_creation_info.get('Title')} into SharePoint.")
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
    st.title("Upload Excel File to SharePoint")
    
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

if __name__ == "__main__":
    app()