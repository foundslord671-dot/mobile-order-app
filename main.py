import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VendorSpace", layout="centered")

# Use your exact ID string
MASTER_SHEET_ID = "1I0672UQXrjuFRBK_dAgHWN5gnqQoc-8sT0iPyuQnLeE"
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def get_master_registry():
    try:
        client = get_gspread_client()
        # Direct connection
        spreadsheet = client.open_by_key(MASTER_SHEET_ID)
        return spreadsheet.sheet1.get_all_records()
    except Exception as e:
        st.error(f"FATAL ERROR: {type(e).__name__} - {str(e)}")
        # Debugging step: print the ID to the terminal to ensure it's correct
        print(f"DEBUG: Attempting to connect to Sheet ID: {MASTER_SHEET_ID}")
        return None

def authenticate_vendor(email):
    registry = get_master_registry()
    if registry is None: return None
    return next((v for v in registry if v.get('email') == email), None)

# --- APP INTERFACE ---
st.title("🚀 VendorSpace")
email_input = st.text_input("Enter business email")

if st.button("Login"):
    vendor = authenticate_vendor(email_input)
    if vendor and vendor.get('status') == 'Active':
        st.success(f"Welcome, {vendor.get('vendor_name')}!")
    else:
        st.error("Account not found, pending, or access denied.")
