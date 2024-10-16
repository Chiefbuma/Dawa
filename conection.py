import streamlit as st
from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
from IPython.display import display
import calendar
import numpy as np
import plotly.express as px
from IPython.display import HTML
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
import streamlit_option_menu as option_menu
import plotly.graph_objects as go
import supabase
import streamlit_shadcn_ui as ui
from local_components import card_container
from streamlit_shadcn_ui import slider, input, textarea, radio_group, switch
import logs, Booking,Billing,Dispatch,Receipt,Collection,Transfer, Dashboard,MVCs,Repair




st.set_page_config(page_title="Bliss Healthcare limited", layout="wide")


class MultiApp:

    def __init__(self):
        self.apps = []

    def run():
        # app = st.sidebar(
        with st.sidebar: 
            app = option_menu.option_menu(key="main_key",
            menu_title='DAWA NYUMBANI',
            options=['Account','Bookings','Consultation', 'Dispatch','Receiving','Collection','Transfer','MVCs','Dashboard','Repairs'],
            icons=['house-fill', 'receipt', 'receipt', 'receipt', 'receipt','receipt','receipt','receipt', 'person-circle','receipt'],
            menu_icon='house-fill',
            default_index=0,
            styles={
                "container": {"padding": "15", "background-color": {"grey": "black", "font-size": "10px"}},
                "nav-link": {"color": "Blck", "font-size": "13px", "text-align": "left"},
                "nav-link-selected": {"background-color": "Black"}
            }
        )       
            
        if app == "Account":
            logs.app()
        if app == "Bookings":
            Booking.app()
        if app == "Consultation":
            Billing.app()  
        if app == "Dispatch":
            Dispatch.app()  
        if app == "Receiving":  
            Receipt.app()  
        if app == "Collection":
           Collection.app()
        if app == "Dashboard":
            Dashboard.app()   
        if app == "Transfer":
            Transfer.app()   
        if app == "MVCs":
            MVCs.app() 
        if app == "Repairs":
            Repair.app()   

    run()            
        
