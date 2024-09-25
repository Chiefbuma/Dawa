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
from st_aggrid import AgGrid, GridOptionsBuilder,JsCode
from IPython.display import HTML
import conection
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
            location=st.session_state.Region
            staffnumber=st.session_state.staffnumber
            department = st.session_state.Department
                
            def init_connection():
                url = "https://effdqrpabawzgqvugxup.supabase.co"
                key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZmRxcnBhYmF3emdxdnVneHVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA1MTQ1NDYsImV4cCI6MjAyNjA5MDU0Nn0.Dkxicm9oaLR5rm-SWlvGfV5OSZxFrim6x8-QNnc2Ua8"
                return create_client(url, key)

            supabase = init_connection()

            if supabase:
                st.session_state.logged_in = True
               

                Allresponse = supabase.from_('Home_Delivery').select('*').execute()
                
                mainall = pd.DataFrame(Allresponse.data)
                
                response = supabase.from_('usersD').select('*').eq('staffnumber', staffnumber).execute()
                usersD_df = pd.DataFrame(response.data)
                
                staffname = usersD_df['staffname'].iloc[0]
                
                # Get a list of unique values in the 'Cycle' column
                Cycle = mainall['Cycle'].unique().tolist()
                
                with card_container(key="collect3"):
                    cols = st.columns([4,1])
                    with cols[1]:
                        with st.container():
                            choice = st.selectbox('Select Cycle', Cycle) 
                            if choice : 
                                AllTrans_df=mainall[mainall['Cycle'] == choice]
                                    
                                if department !="Pharmacy":
                                    Main_df = AllTrans_df
                                           
                                else:   
                                    Main_df = AllTrans_df[
                                            (AllTrans_df['Location'] == location)]
                    with cols[0]:
                        cols = st.columns([4,1])
                        with cols[0]:
                            ui.card(
                                     content=location,
                                    key="MCcard3"
                                ).render()
                            
                      
                container = st.container(border=True, height=500)
                with container:
                
                
                    # Create a new column that indicates whether the CollectionStatus is 'Fully'
                    Main_df['Full_Collection'] = Main_df['Collection status'].isin(['Full']).astype(int)
                    
                    
                    # Create a new column that indicates whether the CollectionStatus is 'Fully'
                    Main_df['Partial_Collection'] = Main_df['Collection status'].isin(['Partial']).astype(int)
                    
                    # Create a new column that indicates whether the CollectionStatus is 'Fully'
                    #Main_df['TransIn'] = Main_df['Location'] == Main_df['TransIn']
                    
                    
                    Telesumamry_df = Main_df.rename(columns={
                        'UHID':'UHID',
                        'Patientname':'Patientname',
                        'mobile':'mobile',
                        'DoctorName': 'Doctor',
                        'Booked By':'Cordinator',
                        'Dispatched By':'WareHouse',
                        'Location':'Medical Centre',
                        'Dispensed By':'Pharmatech.',
                        'Booking status': 'Booked',
                        'Transfer Status':'Total',
                        'Consultation Status': 'Consulted',
                        'Received Status': 'Received',
                        'Dispatched status': 'Dispatched',
                        'Collection Date':'Date',
                        'Partial_Collection':'Partial',
                        'Full_Collection':'Full',
                        'Month': 'Month',
                        'MVC':'MVC',
                        "Cycle":'Cycle'
                    })
                    
                    
                    Telesumamry_df['TransIn'] = (Telesumamry_df['Medical Centre'] == Telesumamry_df['Transfer To']).astype(int)
                    Telesumamry_df['TransOut'] = (Telesumamry_df['Medical Centre'] == Telesumamry_df['Transfer From']).astype(int)
                    
                    Telesumamry_df['Collected'] = ((Telesumamry_df['Collection status'] == "Full") | (Telesumamry_df['Collection status'] == "Partial")).astype(int)
                    
                    Telesumamry_df['Received2'] = (Telesumamry_df['Received Status'] == "Received").astype(int)

                  
                    # Create a new column that indicates whether the value in 'MVC' has the same type and length as the target value
                    # Create a new column that indicates whether the value in 'MVC' has a length of 13 digits
                    Telesumamry_df['ValidMVC'] = Telesumamry_df['MVC'].apply(lambda x: len(str(x)) == 13).astype(int)

                    Target=3827
                    Booked_calc = Main_df [Main_df['Booking status'] == 'Booked']
                    Booked= int(Booked_calc.shape[0])
                    Book_rate= (round(Booked/Target,2)*100)
                    Book_rate= "{:.0f}%".format(Book_rate)
                    
                    
                    Consulted_calc = Telesumamry_df [Telesumamry_df['Consulted'] == 'Consulted']
                    Consulted= int(Consulted_calc.shape[0])
                    cons_rate= (round(Consulted/Booked,2)*100)
                    cons_rate= "{:.0f}%".format(cons_rate)
                    
                    Dispatched_calc = Telesumamry_df [Telesumamry_df['Dispatched'] == 'Dispatched']
                    Dispatched= int(Dispatched_calc.shape[0])
                    dip_rate= (round(Dispatched/Consulted,2)*100)
                    dip_rate= "{:.0f}%".format(dip_rate)
                    
                    
                    Received_calc = Telesumamry_df [Telesumamry_df['Received'] == 'Received']
                    Received= int(Received_calc.shape[0])
                    rev_rate= (round(Received/Dispatched,2)*100)
                    rev_rate= "{:.0f}%".format(rev_rate)
                

                    full_calc =Telesumamry_df['Full'].sum()
                    Full= full_calc
                    
                    Partial_calc = Telesumamry_df['Partial'].sum()
                    Partial= Partial_calc
                    
                    Collected=Partial_calc +full_calc
                    col_rate= (round(Collected/Received,2)*100)
                    col_rate= "{:.0f}%".format(col_rate)
                    
                    
            
                    #Group by 'Cycle' and count the occurrences for each status
                    summary_df = Telesumamry_df.groupby(['Medical Centre','Cycle']).agg({
                        'Booked': 'count',
                        'Consulted': 'count',
                        'Dispatched': 'count',
                        'Received2': 'sum',
                        'Collected':'sum',
                        'TransIn':'sum',
                        'TransOut':'sum',
                        'ValidMVC':'sum'
            
                    }).reset_index()
                
       
                    #CONSULTED
                    # Group by 'Doctor' and count the occurrences for each status
                    consulted_df = Telesumamry_df.groupby('Doctor').agg({
                        'Booked': 'count',
                        'Consulted': 'count'
                    
                    }).reset_index()
                    
                    # Calculate Arch%
                    consulted_df['Arch%'] = (consulted_df['Consulted'] / consulted_df['Booked'].replace(0, pd.NA)) * 100
                    consulted_df = consulted_df.sort_values(by='Arch%', ascending=False)
                    consulted_df['Arch%'] = consulted_df['Arch%'].fillna(0)  # Replace NaN with 0
                    # Convert to string with % symbol
                    consulted_df['Arch%'] = consulted_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                    
                    
                    #Group by 'Doctor' and count the occurrences for each status
                    Received_df = Telesumamry_df.groupby('Medical Centre').agg({
                    'Dispatched': 'count',
                    'Received': 'count'
                        
                    }).reset_index()
                    
                    
                    # Calculate Arch%
                    summary_df['Rvd%'] = (summary_df['Received'] / summary_df['Dispatched'].replace(0, pd.NA)) * 100
                    summary_df['Rvd%'] = summary_df['Rvd%'].fillna(0)  # Replace NaN with 0
                    # Convert to string with % symbol
                    summary_df['Rvd%'] = summary_df['Rvd%'].apply(lambda x: f"{x:.0f}%")
                    
                    
                    #Group by 'Doctor' and count the occurrences for each status
                    Dispatch_df = Telesumamry_df.groupby('Medical Centre').agg({
                        'Consulted': 'count',
                        'Dispatched': 'count'
                    }).reset_index()
                    
                    # Calculate Arch%
                    Dispatch_df['Arch%'] = (Dispatch_df['Consulted'] / Dispatch_df['Dispatched'].replace(0, pd.NA)) * 100
                    Dispatch_df = Dispatch_df.sort_values(by='Arch%', ascending=False)
                    Dispatch_df['Arch%'] = Dispatch_df['Arch%'].fillna(0)  # Replace NaN with 0
                    # Convert to string with % symbol
                    Dispatch_df['Arch%'] = Dispatch_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                    
                
                    #BOOKING
                    #Group by 'Doctor' and count the occurrences for each status
                    Booking_df = Telesumamry_df.groupby('Cordinator').agg({
                        'Booked': 'count'
                    }).reset_index()
                    
                    # Calculate Arch%
                    Booking_df['Target'] = round(3827 / 10, 0)
                    
                    # Calculate Arch%
                    Booking_df['Arch%'] =(Booking_df['Booked'] / Booking_df['Target'].replace(0, pd.NA)) * 100
                    Booking_df['Arch%'] = Booking_df['Arch%'].fillna(0)  # Replace NaN with 0
                    # Convert to string with % symbol
                    Booking_df['Arch%']= Booking_df['Arch%'].apply(lambda x: f"{x:.0f}%")
                    
                    #COLLECTION
                    #Group by 'Doctor' and count the occurrences for each status   
                    Collection_df = Telesumamry_df.groupby('Medical Centre').agg({
                        'Received': 'count',
                        'Collected': 'count'
                    
                    }).reset_index()
                    
                                    # Ensure 'Collected' and 'Received' columns are numeric
                    summary_df['Collected'] = pd.to_numeric(summary_df['Collected'], errors='coerce')
                    summary_df['Received'] = pd.to_numeric(summary_df['Received'], errors='coerce')

                    # Calculate 'Arch%' column
                    summary_df['Clt%'] = (summary_df['Collected'] / summary_df['Received']) * 100

                    # Handle any infinite or NaN values resulting from the division
                    summary_df['Clt%'].replace([np.inf, -np.inf, pd.NA,np.nan], 0, inplace=True)
                    
                    # Calculate Arch%
                    summary_df['Clt%']= summary_df['Clt%'].apply(lambda x: f"{x:.0f}%")
                    
                    
                    
                    # Optionally, you can check how many valid entries there are
                    valid_mvc_count = summary_df['ValidMVC'].sum()
                    
                    TransIn_count = summary_df['TransIn'].sum()
                    
                    TransOut_count = summary_df['TransOut'].sum()
                    
                    # Reorder the columns
                    summary_df = summary_df[[
                        "Medical Centre",
                        'Dispatched', 
                        'TransIn',
                        'TransOut',
                        'Received',
                        'Rvd%',
                        'Collected',
                        'ValidMVC',
                         'Clt%'
                    ]]

                    # Reset the index and remove the old index column
                    summary_df = summary_df.reset_index(drop=True)

                    
                    #summary_df['Stocks'] = (summary_df['Received']+ summary_df['TransOut'])

                    # Handle any infinite or NaN values resulting from the division
                    #summary_df['Stocks'].replace([np.inf, -np.inf, pd.NA,np.nan], 0, inplace=True)
                    
                    # Calculate Arch%
                    #summary_df['Stocks']= summary_df['Stocks'].apply(lambda x: f"{x:.0f}")
                    
                
                #COLLECTION
                    #Group by 'Doctor' and count the occurrences for each status
                    Transfer_df = Telesumamry_df.groupby('Medical Centre').agg({
                        'TransOut': 'count',
                        'TransIn': 'count',
                        'Total':'count'
                    
                    }).reset_index()
                    
                    # This assumes you have a function ui.table to display DataFrames
                    #ui.table(data=Received_df, maxHeight=300)
                    #st.write(grouped_df)   
                
                    coll = st.columns([1.2,4.5,1.5])
                    with coll[0]:
                        colm=st.columns(3)
                        with colm[0]:
                            with st.container():
                                    Bok_label = "Booked"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:16px; font-weight:bold; color:black;">
                                                {Bok_label}
                                            </div>
                                            <div style="font-size:20px; font-weight:bold; color:black;">
                                            {Booked}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{Book_rate}</span>
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                                    
                            with st.container():
                                    Con_label = "Consulted"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:16px; font-weight:bold; color:black;">
                                                {Con_label}
                                            </div>
                                            <div style="font-size:20px; font-weight:bold; color:black;">
                                                {Consulted}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{cons_rate}</span>
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
        
                            with st.container():
                                    Dis_label = "Dispatched"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:16px; font-weight:bold; color:black;">
                                                {Dis_label}
                                            </div>
                                            <div style="font-size:20px; font-weight:bold; color:black;">
                                                {Dispatched}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{dip_rate}</span>
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                            with st.container():
                                    Rec_label = "Received"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:16px; font-weight:bold; color:black;">
                                                {Rec_label}
                                            </div>
                                            <div style="font-size:20px; font-weight:bold; color:black;">
                                                {Received}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{rev_rate}</span>
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                            with st.container():
                                    Collect_label = "Collected"
                                    full_label = "Full-"
                                    Partial_label = "Partial-"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:10px; border-radius:10px; width:200px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:16px; font-weight:bold; color:black;">
                                                {Collect_label}
                                            </div>
                                            <div style="font-size:18px; font-weight:bold; color:black;">
                                            {full_label} {Full}
                                            </div>
                                            <div style="font-size:18px; font-weight:bold; color:black;">
                                            {Partial_label}{Partial}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{col_rate}</span>
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                            
                    with coll[1]:
                        with st.container():
                                    Collect_label = "Sumamry of Transactions"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:1px; border-radius:5px; width:800px; border: 0px  white; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                        st.write(summary_df)
                                
                
                with coll[2]:
                    mvc_label = "Valid MVCs"
                    Mvc=valid_mvc_count
                    mvc_rate=(valid_mvc_count/(Full+Partial))*100
                    mvc_rate="{:.0f}%".format(mvc_rate)
                    st.markdown(
                        f"""
                        <div style="background-color:white; padding:10px; border-radius:10px; width:220px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                            <div style="font-size:16px; font-weight:bold; color:black;">
                                {mvc_label}
                            </div>
                            <div style="font-size:18px; font-weight:bold; color:black;">
                            {Mvc}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{mvc_rate}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    Collect_label = "Footfalls"
                    full_label = "Full-"
                    Partial_label = "Partial-"
                    ff_rate=(Full+Partial)/Target*100
                    ff_rate="{:.0f}%".format(ff_rate)
                    st.markdown(
                        f"""
                        <div style="background-color:white; padding:10px; border-radius:10px; width:220px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                            <div style="font-size:16px; font-weight:bold; color:black;">
                                {Collect_label}
                            </div>
                            <div style="font-size:18px; font-weight:bold; color:black;">
                            {Full+Partial}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{ff_rate}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                    Collect_label = "Revenue"
                    Rev_tt = (Full + Partial) * 3000  # Calculate total revenue
                    Rev_fom = "{:,.0f}".format(Rev_tt)
                    fin_rate = (Rev_tt / (Target * 3000)) * 100  # Calculate the final rate as a percentage
                    fin_rate = "{:.0f}%".format(fin_rate)  # Format the final rate as a percentage string

                    st.markdown(
                        f"""
                        <div style="background-color:white; padding:10px; border-radius:10px; width:220px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                            <div style="font-size:16px; font-weight:bold; color:black;">
                                {Collect_label}
                            </div>
                            <div style="font-size:18px; font-weight:bold; color:black;">
                            {Rev_fom}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:green; font-weight:bold;">{fin_rate}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    with st.container():
                                    TransIn_label = "Transfer In"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:12.5px; border-radius:10px; width:220px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:18px; font-weight:bold; color:black;">
                                                {TransIn_label}
                                            </div>
                                            <div style="font-size:18px; font-weight:bold; color:black;">
                                                {TransIn_count}
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                )
                                    
                    with st.container():
                                    TransOut_label = "Transfer Out"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:12.5px; border-radius:10px; width:220px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">
                                            <div style="font-size:18px; font-weight:bold; color:black;">
                                                {TransOut_label}
                                            </div>
                                            <div style="font-size:20px; font-weight:bold; color:black;">
                                                {TransOut_count}
                                            </div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                        )
                    
                    #Group by 'Doctor' and count the occurrences for each status   
                    MVC_df = Main_df.groupby('Cycle').agg({
                        'Received Status': 'count',
                        'Collection status': 'count'
                    
                    }).reset_index()
                    
                    MVC_df = MVC_df.rename(columns={
                        'Collection status':'Footfalls'})
                
                    MVC_df['Revenue']=MVC_df['Footfalls']*3000

            
                    Revenue_df=MVC_df[['Cycle','Footfalls','Revenue']]
                    
                    #st.write(Revenue_df)
                            
                with st.expander(label="Click here to Track Patient status"):
                    with card_container(key="mew"):  
                        
                        container = st.container(border=True, height=400)
                        with container:
                            display_only_renderer = JsCode("""
                                class DisplayOnlyRenderer {
                                    init(params) {
                                        this.params = params;
                                        this.eGui = document.createElement('div');

                                        // Set the width and height of the div
                                        this.eGui.style.width = '200px'; // Adjust the width as needed
                                        this.eGui.style.height = '20px'; // Adjust the height as needed

                                        this.eGui.innerText = this.params.value || '';
                                    }

                                    getGui() {
                                        return this.eGui;
                                    }
                                }
                                """)
                            
                            display_only_rendererView = JsCode("""
                                class DisplayOnlyRenderer {
                                    init(params) {
                                        this.params = params;
                                        this.eGui = document.createElement('div');

                                        // Set the width and height of the div
                                        this.eGui.style.width = '5px'; // Adjust the width as needed
                                        this.eGui.style.height = '20px'; // Adjust the height as needed

                                        this.eGui.innerText = this.params.value || '';
                                    }

                                    getGui() {
                                        return this.eGui;
                                    }
                                }
                                """)
                            
                                    
                            sumamry_df = Main_df.rename(columns={
                                'UHID':'UHID',
                                'Patientname':'Patientname',
                                'DoctorName': 'Doctor',
                                'Booked By':'Cordinator',
                                'mobile':'mobile',
                                'Dispatched By':'WareHouse',
                                'Location':'Medical Centre',
                                'Dispensed By':'Pharmatech.',
                                'Booking status': 'Booked',
                                'Transfer Status':'Total',
                                'Transfer To':'TransTo',
                                'Transfer From':'TransFrom',
                                'Consultation Status': 'Consulted',
                                'Dispatched status':'Dispatch',
                                'Dispatched Date':'Dispatched Date',
                                'Received Status': 'Received',
                                'Collection Date':'Date',
                                'Partial_Collection':'Partial',
                                'Full_Collection':'Full',
                                'Collection status': 'Collected',
                                'Month': 'Month',
                                'MVC':'MVC',
                                "Cycle":'Cycle'})
                    
                            # Create the DataFrame with the required columns
                            status_df = sumamry_df[[
                                "Patientname",
                                "UHID",
                                "mobile",
                                "Medical Centre","Cycle",
                                 "Consulted","Booked","Dispatch",
                                 'Dispatched Date', 
                                'Received',
                                'TransFrom',
                                'TransTo',
                                'Collected',
                                'Date',
                                'MVC'
                            ]]
                            

                            colsearch = st.columns(4)
                            
                            with colsearch [0]:

                                    
                                    st.markdown(
                                        f"""
                                        <div style="background-color:white; padding:20px; border-radius:5px; width:1250px; border: 0.5px solid grey; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4); margin-bottom:5px;">

                                        """, 
                                        unsafe_allow_html=True
                                    )
                                
                            st.write(status_df)
    
        else:
            st.write("You  are  not  logged  in. Click   **[Account]**  on the  side  menu to Login  or  Signup  to proceed")
    except APIError as e:
            st.error("Cannot connect, Kindly refresh")
            st.stop() 
            
            
