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
from sharepoint import SharePonitLsist
from postgrest import APIError
from IPython.display import HTML
import logging
from streamlit_dynamic_filters import DynamicFilters
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode



def app():
    
    try:

        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False 
            st.write(f"""<span style="color: red;">
                        You are not Logged in,click account to  Log in/Sign up to proceed.
                    </span>""", unsafe_allow_html=True)
        
            # Initialize session state if it doesn't exist
                    
        if st.session_state.is_authenticated:
            
            # get clients sharepoint list
            st.cache_data(ttl=80, max_entries=2000, show_spinner=False, persist=False, experimental_allow_widgets=False)
            def load_new():
                columns = [
                    "Date of report",
                    "Name of Staff",
                    "Department",
                    "Month",
                    "Date Number ",
                    "Clinic",
                    "Departmental report",
                    "Details",
                    "Report",
                    "MainLink flow",
                    "ATTACHED",
                    "MainLINK",
                    "MainItem",
                    "Labor",
                    "Amount on the Quotation",
                    "RIT Approval",
                    "RIT Comment",
                    "RIT labour",
                    "Facility Approval",
                    "Facility comments",
                    "Facility Labor",
                    "Time Line",
                    "Projects Approval",
                    "Project Comments",
                    "Project Labor",
                    "Admin Approval",
                    "Admin Comments",
                    "Admin labor",
                    "Approved amount",
                    "Finance Amount",
                    "STATUS",
                    "Approver",
                    "TYPE",
                    "Days",
                    "Disbursement",
                    "MainStatus",
                    "Modified",
                    "Modified By",
                    "Created By",
                    "ID",
                    "Email",
                    "MAINTYPE",
                    "Attachments",
                    "LinkEdit",
                    "UpdateLink",
                    "PHOTOS",
                    "QUOTES",
                    "Title",
                    "MonthName",
                    "Centre Manager Approval",
                    "Biomedical Head Approval"

                ]
                
                try:
                    clients = SharePonitLsist().connect_to_list(ls_name='Maintenance Report', columns=columns)
                    df = pd.DataFrame(clients)
                    
                    # Ensure all specified columns are in the DataFrame, even if empty
                    for col in columns:
                        if col not in df.columns:
                            df[col] = None

                    return df
                except APIError as e:
                    st.error("Connection not available, check connection")
                    st.stop()       
           
            Main_df = load_new()
            
            Department_df= Main_df[['Departmental report','Approved amount','Admin Approval','Month']]

            # Filter Department_df where 'Admin Approval' is 'Approved'
            approved_department_df = Department_df[Department_df['Admin Approval'] == 'Approved']

            # Group by 'Departmental report' and 'Month', and sum 'Approved amount'
            department_sum_df = approved_department_df.groupby(['Departmental report', 'Month'])['Approved amount'].sum().reset_index()

            # Rename the columns
            department_sum_df.columns = ['Category', 'Month', 'Value']

            
            # Filter the Main_df DataFrame to get the "departmental report" column
            Isssue_report_df =  Main_df["Report"]

            # Assuming departmental_report_df is your DataFrame
            Isssue_counts =  Isssue_report_df.value_counts().reset_index()
            
            # Rename the columns to "Category" and "No."
            Isssue_counts.columns = ["Category", "No."]
            
            # Convert "No." column to integers
            Isssue_counts["No."] = Isssue_counts["No."].astype(int)
            
            #ISSUE REPORT
            # Filter the Main_df DataFrame to get the "departmental report" column
    

            def get_month_options():
                current_year = datetime.now().year
                current_month = datetime.now().month
                month_names = [
                    datetime(current_year, month, 3).strftime('%B')
                    for month in range(3, current_month + 1)
                ]
                month_names.insert(0, "Select Month")
                return month_names

            month_options = get_month_options()
            cols = st.columns(2)
            with cols[0]:
                ui.card(
                        content="Bliss Healthcare Maintenance Dashboard",
                        key="MCcard3"
                    ).render()
            with cols[1]:
                choice = ui.select(options=month_options)
                
                if choice and choice != "Select Month":
                    
                    Main_df = load_new()
                    
                    # Map the month name back to its numeric value
                    month_number = datetime.strptime(choice, "%B").month

                    approved_main_df = Main_df[(Main_df['Admin Approval'] == 'Approved') & (Main_df['Month'] == month_number)]
                    Selected_df=Main_df[Main_df['Month'] == month_number]
                    Main_df=Main_df[Main_df['Month'] == month_number]
                    
                    department_All=department_sum_df[department_sum_df['Month'] == month_number]
                    
                    Centre_df=Main_df[(Main_df['Admin Approval'] == 'Approved') & (Main_df['Month'] == month_number)]
                    
                if choice and choice == "Select Month":
                    
                    
                    Selected_df = Main_df[ Main_df['Month'] < 13]
                    approved_main_df = Main_df[Main_df['Title'] != '']
                    Centre_df=Main_df[(Main_df['Admin Approval'] == 'Approved') & (Main_df['Month']< 13)]
                    
                    department_All=department_sum_df
                    
                    
            with card_container(key="Main1"):
                
                #ALL SUMMARY
                Total_requests = Main_df["ID"].nunique()
                
                Total_Value = Main_df.groupby('ID')["Amount on the Quotation"].sum().sum()

                pending_requests_calc = Main_df [Main_df ["MainStatus"] == "Pending"]
                pending_request = int(pending_requests_calc.shape[0])
                
                
                pending_value=pending_requests_calc.groupby('ID')["Amount on the Quotation"].sum().sum()

                closed_requests_calc =  Main_df [Main_df ["MainStatus"] == "Closed"]
                closed_request = int(closed_requests_calc.shape[0])

                numeric_days_pending = Main_df["Days"].apply(pd.to_numeric, errors="coerce")
                Main_df["Days"] = numeric_days_pending
                Main_df.dropna(subset=["Days"], inplace=True) 
                
                Director_Approved = Main_df[Main_df["Admin Approval"] == "Approved"]
                Dir_Approved_value = '{:,.0f}'.format(Director_Approved["Approved amount"].sum())
                Dir_Approved_request = Director_Approved["ID"].nunique()

                if Main_df is not None:
                    cols = st.columns(4)
                    with cols[0]:
                        ui.card(title="Total Request", content=Total_requests, key="Revcard10").render()
                    with cols[1]:
                        ui.card(title="Closed Request", content=closed_request , key="Revcard11").render()
                    with cols[2]:
                        ui.card(title="Pending Request", content=pending_request, key="Revcard12").render()
                    with cols[3]:
                        ui.card(title="Approved Value:", content=Dir_Approved_value, key="Revcard13").render() 
                                        

                    
                    @st.cache_data(ttl=600, max_entries=100, show_spinner=False, persist=False, experimental_allow_widgets=False)
                    def load_new():
                            New = SharePonitLsist().connect_to_list(ls_name='Maintenance Report')
                            return pd.DataFrame(  New )
                        
                    df_check=load_new()
                    
                    Overall_df= df_check[['Clinic','Departmental report','Title','Admin Approval']]
                    
                    Overall_df['Requests'] = int(Overall_df['Title'].nunique())
                    
                    # Create a new column that indicates whether the CollectionStatus is 'Fully'
                    Overall_df['Approved'] = Overall_df['Admin Approval'].isin(['Approved']).astype(int)
                    
                    Overall_df['Pending'] = (~Overall_df['Admin Approval'].isin(['Approved'])).astype(int)

                
                
                    # Create a new column that indicates whether the CollectionStatus is 'Fully'
                    #Main_df['TransIn'] = Main_df['Location'] == Main_df['TransIn']
                    
                    #Group by 'Cycle' and count the occurrences for each status
                    summary_df = Overall_df.groupby(['Clinic']).agg({
                        'Requests': 'count',
                        'Approved':'sum',
                        'Pending':'sum'
                    }).reset_index()
                    
                
                    cols = st.columns(2)
                    with cols[1]:
                
                        # Get unique items in the "Report" column
                        unique_reports = approved_main_df["Report"].unique()

                        # Create an empty dictionary to store the sum of approved amounts for each unique report
                        report_sum = {}

                        # Iterate over each unique report and calculate the sum of approved amounts
                        for report in unique_reports:
                            sum_approved_amount = approved_main_df[approved_main_df["Report"] == report]["Approved amount"].sum()
                            report_sum[report] = sum_approved_amount

                        # Convert the dictionary to a DataFrame for easier visualization
                        report_sum_df = pd.DataFrame(list(report_sum.items()), columns=["Item", "Cost"])
                        
                        #ALL SUMMARY
                        Finance_Approved = Selected_df[ Selected_df["Biomedical Head Approval"] == "Approved"]
                        Finance_Approved_value = '{:,.0f}'.format(Finance_Approved["Approved amount"].sum())
                        Finance_Approved_request =  Finance_Approved["ID"].nunique()
                        
                        Finance_pending =  Selected_df[( Selected_df["Biomedical Head Approval"].isnull()) & (Selected_df["Projects Approval"] == "Approved")]
                        Fin_pending_request = Finance_pending["ID"].nunique()
                        
                        
                        Director_Approved = Selected_df[ Selected_df["Admin Approval"] == "Approved"]
                        Dir_Approved_value = '{:,.0f}'.format(Director_Approved["Approved amount"].sum())
                        Dir_Approved_request = Director_Approved["ID"].nunique()

                        Director_pending =  Selected_df[( Selected_df["Admin Approval"].isnull()) & (Selected_df["Projects Approval"] == "Approved")]
                        Dir_pending_request = Director_pending["ID"].nunique()

                        Director_Rejected = Selected_df[ Selected_df["Admin Approval"] == "Rejected"]
                        Dir_rejected_request = Director_Rejected["ID"].nunique()

                        Ops_Approved =  Selected_df[ Selected_df["RIT Approval"] == "Approved"]
                        Ops_Approved_value = '{:,.0f}'.format(Ops_Approved["Approved amount"].sum())
                        Ops_Approved_request = Ops_Approved["ID"].nunique()

                        Ops_pending =  Selected_df[Selected_df["RIT Approval"].isnull()]
                        Ops_pending_request = Ops_pending["ID"].nunique()

                        Ops_rejected =  Selected_df[Selected_df["RIT Approval"] == "Rejected"]
                        Ops_rejected_request = Ops_rejected["ID"].nunique()

                        Fac_Approved =  Selected_df[Selected_df["Facility Approval"] == "Approved"]
                        Fac_Approved_value = '{:,.0f}'.format(Fac_Approved["Approved amount"].sum())
                        Fac_Approved_request = Fac_Approved["ID"].nunique()

                        Fac_pending =  Selected_df[( Selected_df["Facility Approval"].isnull()) & ( Selected_df["RIT Approval"] == "Approved")]
                        Fac_pending_request = Fac_pending["ID"].nunique()

                        Fac_rejected =  Selected_df[ Selected_df["Facility Approval"] == "Rejected"]
                        Fac_rejected_request = Fac_rejected["ID"].nunique()

                        Pro_Approved = Selected_df[Selected_df["Projects Approval"] == "Approved"]
                        Pro_Approved_value = '{:,.0f}'.format(Pro_Approved["Approved amount"].sum())
                        Pro_Approved_request = Pro_Approved["ID"].nunique()

                        Pro_pending =  Selected_df[( Selected_df["Projects Approval"].isnull()) & (Selected_df["Facility Approval"] == "Approved")]
                        Pro_pending_request = Pro_pending["ID"].nunique()

                        Pro_rejected = Selected_df[Selected_df["Projects Approval"] == "Rejected"]
                        Pro_rejected_request = Pro_rejected["ID"].nunique()
                                                
                        data = [
                            {"Approver": "Director", "Approved.":Dir_Approved_request, "Pending": Dir_pending_request,"Rejected": Dir_rejected_request },
                            {"Approver": "Projects", "Approved.":Pro_Approved_request,  "Pending":Pro_pending_request,"Rejected": Pro_rejected_request },
                            {"Approver": "Cordinator", "Approved.":Fac_Approved_request,  "Pending":Fac_pending_request,"Rejected": Fac_rejected_request },
                            {"Approver": "Operations", "Approved.":Ops_Approved_request,  "Pending":Ops_pending_request ,"Rejected": Ops_rejected_request}
                            # Add more records as needed
                        ]
                        
                        #st.write(New_df)
                        
                        # Creating a DataFrame
                        Approval_df = pd.DataFrame(data)
                        
                        ui.table(data=Approval_df, maxHeight=300)
                        
                    with cols[0]:
                        
                        
                        st.write(summary_df)

                    with card_container(key="gallery1"):

                        
                        st.markdown('<div style="height: 0px; overflow-y: scroll;">', unsafe_allow_html=True)
                        @st.cache_data(ttl=600, max_entries=100, show_spinner=False, persist=False, experimental_allow_widgets=False)
                        def load_new():
                                New = SharePonitLsist().connect_to_list(ls_name='Maintenance Report')
                                return pd.DataFrame(  New )
                            
                        df_main=load_new()
                        
                        data_df= df_main[['ID','Date of report','Clinic','Details','MainStatus','Approver','MonthName']]
                        
                     
              
                            
                        ui.table(data=df_main, maxHeight=300)
                        
                        # Convert 'bill_date' to datetime type
                        data_df['Date of report'] = pd.to_datetime(data_df['Date of report']).dt.date
                                            
                        # Extract just the month name
                        data_df['MonthName'] = data_df['MonthName'].str.split(';#').str[1]
                    
                        data_df = data_df.rename(columns={
                            'ID': 'Ticket',
                            'Date of report':'Date',
                            'Clinic': 'Facility',
                            'MainStatus': 'Status',
                            'Approver': 'Pending With'
                            
                        })
                        # Fill NaN/NA values with an empty string
                        
                        data_df.fillna('', inplace=True)
                        
                        
                           
                
                    metrics = [
                        {"label": "Total", "value": Total_requests},
                        {"label": "Closed", "value": closed_request},
                        {"label": "Pending", "value": pending_request},
                        {"label": "Value", "value": Total_Value}
                    ]

                    fig_data_cards = go.Figure()

                    for i, metric in enumerate(metrics):
                        fig_data_cards.add_trace(go.Indicator(
                            mode="number",
                            value=metric["value"],
                            number={'font': {'size': 25, 'color': 'white'}},
                            domain={'row': i, 'column': 0},
                            title={'text': metric["label"],'font': {'size': 20,'color': 'white'}},
                            align="center"
                        ))

                    fig_data_cards.update_layout(
                        grid={'rows': len(metrics), 'columns': 1, 'pattern': "independent"},
                        template="plotly_white",
                        height=100*len(metrics),
                        paper_bgcolor='rgba(0, 131, 184, 1)',
                        plot_bgcolor='rgba(0, 137, 184, 1)',
                        uniformtext=dict(minsize=40, mode='hide'),
                        margin=dict(l=20, r=20, t=50, b=5)
                    )

                    st.markdown(
                        """
                        <style>
                        .st-cd {
                            border: 1px solid #e6e9ef;
                            border-radius: 100px;
                            padding: 10px;
                            margin-bottom: 10px;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.write("You  are  not  logged  in. Click   **[Account]**  on the  side  menu to Login  or  Signup  to proceed")
    
    
    except APIError as e:
            st.error("Cannot connect, Kindly refresh")
            st.stop() 
