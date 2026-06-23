import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURATION ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

# --- AUTHENTICATION & DATA ROUTING ---
def get_master_registry():
    client = get_gspread_client()
    # The 'Master_Registry' sheet tracks all vendors and their unique database keys
    return client.open("Master_Registry").sheet1.get_all_records()

def authenticate_vendor(email):
    registry = get_master_registry()
    return next((v for v in registry if v['email'] == email), None)

# --- APP UI ---
st.set_page_config(page_title="VendorSpace SaaS", layout="wide")
st.title("🚀 VendorSpace: Multi-Vendor Platform")

# Session State for Login
if 'vendor' not in st.session_state:
    st.subheader("Vendor Portal Login")
    email_input = st.text_input("Enter your business email")
    if st.button("Login"):
        vendor_info = authenticate_vendor(email_input)
        if vendor_info and vendor_info['status'] == 'Active':
            st.session_state['vendor'] = vendor_info
            st.rerun()
        else:
            st.error("Access Denied: Account not found or inactive.")
    
    # --- ADMIN ENTRY POINT ---
    with st.expander("Admin Login"):
        admin_key = st.text_input("Admin Password", type="password")
        if admin_key == st.secrets.get("ADMIN_PASSWORD"):
            st.session_state['admin'] = True
            st.rerun()

else:
    # --- AUTHENTICATED VENDOR DASHBOARD ---
    vendor = st.session_state['vendor']
    st.sidebar.title(f"Welcome, {vendor['vendor_name']}")
    
    client = get_gspread_client()
    vendor_sheet = client.open_by_key(vendor['sheet_id']).sheet1
    
    tab1, tab2 = st.tabs(["📊 Orders", "➕ Add Product"])
    
    with tab1:
        st.subheader("Your Orders")
        orders = vendor_sheet.get_all_records()
        if orders:
            st.dataframe(pd.DataFrame(orders))
        else:
            st.info("No orders received yet.")
            
    with tab2:
        st.subheader("Manage Catalog")
        # Logic to append new products to vendor_sheet
        pass

    if st.sidebar.button("Logout"):
        del st.session_state['vendor']
        st.rerun()

# --- ADMIN PANEL ---
if st.session_state.get('admin'):
    st.sidebar.divider()
    st.sidebar.header("Admin Control Panel")
    new_name = st.sidebar.text_input("New Vendor Name")
    new_email = st.sidebar.text_input("New Vendor Email")
    new_key = st.sidebar.text_input("Google Sheet ID")
    
    if st.sidebar.button("Provision New Vendor"):
        # Logic to append to Master_Registry
        st.sidebar.success(f"Provisioned {new_name}")
