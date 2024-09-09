import streamlit as st
import pandas as pd
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import List

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

    # Upload Excel file widget
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

    # If a file is uploaded
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        
        # Convert date columns to the required format
        date_columns = ['BookingDate', 'ConsultationDate', 'DispatchedDate', 'ReceivedDate', 'CollectionDate', 'Booked on']
        available_date_columns = [col for col in date_columns if col in df.columns]
        
        for column in available_date_columns:
            df[column] = pd.to_datetime(df[column]).dt.strftime('%d/%m/%Y')

        # Replace NaN values with blank strings and convert columns to strings
        df = df.fillna('').astype(str)

        # Display the DataFrame to the user
        st.write("Uploaded Data Preview:")
        st.dataframe(df)

        # Submit button to trigger the upload to SharePoint
        if st.button("Submit to SharePoint"):
            ctx = connect_to_sharepoint()
            upload_to_sharepoint(df, ctx)
    else:
        st.write("Please upload an Excel file to proceed.")

if __name__ == "__main__":
    app()
