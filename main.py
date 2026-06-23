import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VendorSpace", layout="centered")

# Use your specific Sheet ID from the URL
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
        # Open directly by ID
        sheet = client.open_by_key(MASTER_SHEET_ID).sheet1
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"Error connecting to Registry: {e}")
        return []

# --- APP LOGIC ---
st.title("🚀 VendorSpace")
email_input = st.text_input("Enter business email")

if st.button("Login"):
    registry = get_master_registry()
    vendor = next((v for v in registry if v.get('email') == email_input), None)
    
    if vendor and vendor.get('status') == 'Active':
        st.success(f"Welcome, {vendor.get('vendor_name')}!")
    else:
        st.error("Account not found, pending, or access denied.")
