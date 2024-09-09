import streamlit as st
import pandas as pd
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
import time
import os

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

        # Constants for SharePoint
        sharepoint_url = "https://blissgvske.sharepoint.com/sites/BlissHealthcareReports/"
        username = "biosafety@blisshealthcare.co.ke"
        password = "Streamlit@2024"
        list_name = 'Home DeliveryCheck'

        # Connect to SharePoint
        ctx_auth = AuthenticationContext(sharepoint_url)
        if ctx_auth.acquire_token_for_user(username, password):
            ctx = ClientContext(sharepoint_url, ctx_auth)
            web = ctx.web
            ctx.load(web)
            ctx.execute_query()
            st.write(f"Connected to SharePoint site: {web.properties['Title']}")
        else:
            st.error(f"Failed to authenticate: {ctx_auth.get_last_error()}")
            return

        # Function to process and upload data to SharePoint
        def process_and_upload_to_sharepoint(df):
            try:
                target_list = ctx.web.lists.get_by_title(list_name)
                ctx.load(target_list)
                ctx.execute_query()

                for index, row in df.iterrows():
                    item_creation_info = row.to_dict()
                    new_item = target_list.add_item(item_creation_info)
                    new_item.update()
                    ctx.execute_query()
                    st.write(f"Inserted row {index + 1} into SharePoint.")
                    time.sleep(0.5)  # Small delay to prevent overloading SharePoint with requests

                st.success("All rows have been inserted successfully.")
            except Exception as e:
                st.error(f"Failed to upload to SharePoint: {str(e)}")

        # Streamlit UI for Excel upload and processing
        st.title("Excel Upload to SharePoint")

        # Upload Excel file widget
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

        # If a file is uploaded
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)

            # Replace NaN values with blank strings and convert columns to strings
            df = df.fillna('').astype(str)

            # Display the DataFrame to the user
            st.write("Uploaded Data Preview:")
            st.dataframe(df)

            # Submit button to trigger the upload to SharePoint
            if st.button("Submit to SharePoint"):
                process_and_upload_to_sharepoint(df)
        else:
            st.write("Please upload an Excel file to proceed.")

    else:
        st.write("You are not logged in. Click **[Account]** on the side menu to Login or Signup to proceed")

