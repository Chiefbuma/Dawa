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
from sharepoint import SharePoint
from postgrest import APIError
from IPython.display import HTML
import main
from streamlit_dynamic_filters import DynamicFilters



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
                    clients = SharePoint().connect_to_list(ls_name='Maintenance Report', columns=columns)
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
                    
                    All_df = load_new()
                    
                    Selected_df = All_df[All_df['Month'] < 13]
                    approved_main_df = Main_df[Main_df['Title'] != '']
                    Main_df=All_df
                    Centre_df=Main_df[(All_df['Admin Approval'] == 'Approved') & (All_df['Month']< 13)]
                    
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
                                        
                    with card_container(key="table2"):
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
                                {"Approver": "Director", "Approved.":Dir_Approved_request, "Value":Dir_Approved_value, "Pending": Dir_pending_request,"Rejected": Dir_rejected_request },
                                {"Approver": "Projects", "Approved.":Pro_Approved_request, "Value":Pro_Approved_value , "Pending":Pro_pending_request,"Rejected": Pro_rejected_request },
                                {"Approver": "Cordinator", "Approved.":Fac_Approved_request, "Value":Fac_Approved_value, "Pending":Fac_pending_request,"Rejected": Fac_rejected_request },
                                {"Approver": "Operations", "Approved.":Ops_Approved_request, "Value":Ops_Approved_value, "Pending":Ops_pending_request ,"Rejected": Ops_rejected_request}
                                # Add more records as needed
                            ]
                            
                            #st.write(New_df)
                            
                            # Creating a DataFrame
                            Approval_df = pd.DataFrame(data)

                            with card_container(key="table1"):
                                
                                def generate_sales_data():
                                    np.random.seed(0)  # For reproducible results
                                    Item = report_sum_df["Item"].apply(lambda x: x.split()[0]).tolist()
                                    Cost = report_sum_df["Cost"].tolist()
                                    return pd.DataFrame({'Item': Item, 'Cost': Cost})
                                with card_container(key="chart2"):
                                    st.vega_lite_chart(generate_sales_data(), {
                                        'title': 'Cost of Repairs -(Based on Approved Amount)',
                                        'mark': {'type': 'bar', 'tooltip': True, 'fill': 'black', 'cornerRadiusEnd': 4 },
                                        'encoding': {
                                            'x': {'field': 'Item', 'type': 'ordinal'},
                                            'y': {'field': 'Cost', 'type': 'quantitative', 'sort': '-x', 'axis': {'grid': False}},
                                        },
                                    }, use_container_width=True)
                            
                            with card_container(key="table1"):
                                with card_container(key="summary"):
            # Define the layout using `ui.input` for inputs and `st.write` for labels
                                    colz = st.columns([1,2,1])
                                    with colz[1]:
                                      st.markdown("### Maintenance Request")
                                    # Column layout for Patient Name
                                    cola = st.columns([2, 6,1])
                                    with cola[0]:
                                        st.write("**Department:**")
                                    with cola[1]:
                                        Department = ui.input(key="Dep")
                                    # Column layout for UHID
                                    colb = st.columns([2, 6,1])
                                    with colb[0]:
                                        st.write("**Report Type:**")
                                    with colb[1]:
                                        Report = ui.input(key="report")
                                    # Column layout for Modality
                                    colc = st.columns([2, 6,1])
                                    with colc[0]:
                                        st.write("**Item:**")
                                    with colc[1]:
                                        Item = ui.input(key="item")

                                    # Column layout for Procedure
                                    cold = st.columns([2, 6,1])
                                    with cold[0]:
                                        st.write("**Description of works:**")
                                    with cold[1]:
                                        description = ui.input(key="works")

                                    # Column layout for Referred By
                                    cole = st.columns([2, 6,1])
                                    with cole[0]:
                                        st.write("**Labour:**")
                                    with cole[1]:
                                        Labor = ui.input(key="Labor")

                                    # Column layout for Facility
                                    colf = st.columns([2, 6,1])
                                    with colf[0]:
                                        st.write("**Total Amount:**")
                                    with colf[1]:
                                        Total = ui.input(key="Total")

                                    # Column layout for MPESA No
                                    colg = st.columns([2, 6,1])
                                    with colg[0]:
                                        st.write("**MPESA Number.:**")
                                    with colg[1]:
                                        MPESA_no = ui.input(key="MPESA_no")
                                    colj=st.columns(7)
                                    with colj[3]:
                                            ui_result = ui.button("Submit", key="btn2")  
                                            if ui_result: 
                                              with st.spinner('Wait! Reloading view...'):
                                                st.cache_data.clear()
                                                            
                        with  cols[0]:
                            with card_container(key="table1"):
                                def generate_sales_data():
                                    np.random.seed(0)  # For reproducible results
                                    Category = department_All["Category"].apply(lambda x: x.split()[0]).tolist()
                                    Value = department_All["Value"].tolist()
                                    return pd.DataFrame({'Category': Category, 'Value': Value})
                                
                                with card_container(key="chart1"):
                                    st.vega_lite_chart(generate_sales_data(), {
                                        'title': 'Cost of Repairs by Category (Based on Approved Amount)',
                                        'mark': {'type': 'arc', 'tooltip': True},
                                        'encoding': {
                                            'theta': {'field': 'Value', 'type': 'quantitative', "sort": "descending", "stack": True},
                                            'radius': {'field': 'Value', 'scale': {'type': 'sqrt', 'zero': True, 'rangeMin': 20}},
                                            'color': {'field': 'Category', 'type': 'nominal', 'scale': {'range': ['blue', 'green', 'red', 'orange', 'purple']}},
                                            'text': {'field': 'Category', 'type': 'nominal'}
                                            
                                        },   
                                        "layer": [{
                                            "mark": {"type": "arc", "innerRadius": 20, "stroke": "#fff"}
                                        }, {
                                            "mark": {"type": "text", "radiusOffset": 10},
                                            "encoding": {
                                            
                                                'theta': {'field': 'Value', 'type': 'quantitative', "stack": True},
                                                "legend":False
                                            }
                                        }]


                                    }, use_container_width=True)
                    
                            
                            # Group by 'Facility' and 'Issue', and sum 'Amount on the Quotation' and 'Approved amount'
                            Mcgroup_df = Centre_df.groupby(['Clinic','Departmental report']).agg({
                                'Amount on the Quotation': 'sum',
                                'Approved amount': 'sum'
                    

                            }).reset_index()
                            
                            
                             # Group by 'Facility' and 'Issue', and sum 'Amount on the Quotation' and 'Approved amount'
                            McNew_df = Centre_df.groupby(['Clinic']).agg({
                                'Amount on the Quotation': 'sum',
                                'Approved amount': 'sum'
                    

                            }).reset_index()
                        

                            # Rename columns
                            McNew_df = McNew_df.rename(columns={
                                'Amount on the Quotation': 'Total Qouted',
                                'Approved amount': 'Total Approved',
                                'Clinic':'Facility',
                                'Pending':'Pending Value'
                                
                                
                            })
                            
                            # Rename columns
                            Mcgroup_df = Mcgroup_df.rename(columns={
                                'Amount on the Quotation': 'Total Qouted',
                                'Approved amount': 'Total Approved',
                                'Clinic':'Facility',
                                'Pending':'Pending Value'
                                
                                
                            })
                            
                            
                            Mcgroup_df["Total Qouted"] =Mcgroup_df["Total Qouted"].apply(lambda x: '{:,.0f}'.format(x))
                            Mcgroup_df["Total Approved"] =Mcgroup_df["Total Approved"].apply(lambda x: '{:,.0f}'.format(x))
                            
                            McNew_df["Total Qouted"] = McNew_df["Total Qouted"].apply(lambda x: '{:,.0f}'.format(x))
                            McNew_df["Total Approved"] = McNew_df["Total Approved"].apply(lambda x: '{:,.0f}'.format(x))
                            
                            
                            selected_option = ui.tabs(options=['All','Capentry', 'Masonry', 'Electrical', 'Plumbing','Utility'], default_value='All', key="kanaries")
                            
                            if selected_option and selected_option != "All":
                            
                                # Filter the Mcgroup_df DataFrame based on the selected option
                                filtered_df = Mcgroup_df[Mcgroup_df['Departmental report'] == selected_option]
                                
                            else:
                                
                                filtered_df = McNew_df
                                
                                
                            container = st.container(border=True, height=185)
                                
                            with container:
                            
                                ui.table(data=filtered_df, maxHeight=300)
                            
                cols=st.columns(10)
                with cols[9]:
                   ui_result = ui.button("Load", key="btn")  
                   if ui_result:   
                       st.cache_data.clear()    
                            
                with cols[8]:
                   ui_pop = ui.button("Pop", key="pop") 
                   popover = st.popover("Filter items") 
                   red = popover.checkbox("Show red items.", True)
                   blue = popover.checkbox("Show blue items.", True)
                   
                   if ui_pop:   
                       st.popover('This is a popup!')  
                                                         
                if 'toggle_value' not in st.session_state:
                    st.session_state.toggle_value = False

                with cols[0]:
                    # Create a checkbox to toggle the value
                    toggle_value = ui.switch(default_checked=st.session_state.toggle_value, label="Show Table", key="switch1")   

                # Store the value of the toggle in the session state
                st.session_state.toggle_value = toggle_value
                
                if "load_state" not in st.session_state:
                        st.session_state.load_state=False
                        
                if toggle_value:
                    st.session_state.load_state=True
                    st.session_state.toggle_value = True
                
                    with card_container(key="gallery1"):

                        
                        st.markdown('<div style="height: 0px; overflow-y: scroll;">', unsafe_allow_html=True)
                        @st.cache_data(ttl=600, max_entries=100, show_spinner=False, persist=False, experimental_allow_widgets=False)
                        def load_new():
                                New = SharePoint().connect_to_list(ls_name='Maintenance Report')
                                return pd.DataFrame(  New )
                            
                        df_main=load_new()
                        
                        data_df= df_main[['ID','Date of report','Clinic','Department','Amount on the Quotation','MainStatus','Approver','MonthName','LinkEdit']]
                        
                        # Convert 'bill_date' to datetime type
                        data_df['Date of report'] = pd.to_datetime(data_df['Date of report']).dt.date
                                            
                        # Extract just the month name
                        data_df['MonthName'] = data_df['MonthName'].str.split(';#').str[1]
                    
                        data_df = data_df.rename(columns={
                            'ID': 'Tkt',
                            'Date of report':'Date',
                            'Clinic': 'Facility',
                            'Department':'Dep',
                            'Amount on the Quotation': 'Amount',
                            'MainStatus': 'Status',
                            'MonthName':'Month',
                            'Approver': 'Approver',
                            'LinkEdit': 'Link'
                        })
                        # Fill NaN/NA values with an empty string
                        
                        data_df.fillna('', inplace=True)
                        
                        # Define the columns to filter
                        filter_columns = ["Tkt", "Approver", "Facility","Issue","Status","Month"]

                        # Create five columnss for arranging widgets horizontally
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        
                        
                        # Create a dictionary to store filter values
                        filters = {column: '' for column in filter_columns}
                        

                        # Create text input widgets for each filter column and arrange them horizontally
                        with col1:
                            filters[filter_columns[0]] = st.text_input(f"Filter {filter_columns[0]}", filters[filter_columns[0]])
                        with col2:
                            filters[filter_columns[1]] = st.text_input(f"Filter {filter_columns[1]}", filters[filter_columns[1]])
                        with col3:
                            filters[filter_columns[2]] = st.text_input(f"Filter {filter_columns[2]}", filters[filter_columns[2]])
                        with col4:
                            filters[filter_columns[3]] = st.text_input(f"Filter {filter_columns[3]}", filters[filter_columns[3]])
                        with col5:
                            filters[filter_columns[4]] = st.text_input(f"Filter {filter_columns[4]}", filters[filter_columns[4]])
                        with col6:
                            filters[filter_columns[5]] = st.text_input(f"Filter {filter_columns[5]}", filters[filter_columns[5]])
                        # Apply filters to the DataFrame
                        filtered_df = data_df
                        for column, filter_value in filters.items():
                            if filter_value:
                                filtered_df = filtered_df[filtered_df[column].str.contains(filter_value, case=False)]

                        # Display the filtered DataFrame using st.data_editor
                        with card_container(key="gallery4"):
                            st.data_editor(
                                filtered_df,
                                column_config={
                                    "Link": st.column_config.LinkColumn(
                                        "Link",
                                        display_text="View"
                                    )
                                },
                                hide_index=True
                            , use_container_width=True)
                                            
                                                       
                    
                    
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
