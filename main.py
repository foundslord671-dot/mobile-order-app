import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="VendorSpace", layout="centered")

# REPLACE THIS with your specific Google Sheet ID from your URL
# It's the long string of letters and numbers between /d/ and /edit
MASTER_SHEET_ID = "1I0672UQXrjuFRBK_dAgHWN5gnqQoc-8sT0iPyuQnLeE"

# Scopes required for Sheets and Drive access
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_gspread_client():
    """Authenticates the Google Sheets client using secrets."""
    # Ensure 'gcp_service_account' is correctly formatted in Streamlit Secrets
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def get_data():
    """Fetches data from the Google Sheet."""
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(MASTER_SHEET_ID).sheet1
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# --- APP INTERFACE ---
st.title("🚀 VendorSpace")
email_input = st.text_input("Enter business email")

if st.button("Login"):
    data = get_data()
    if data:
        # Check if the email exists in the sheet
        vendor = next((item for item in data if item.get('email') == email_input), None)
        
        if vendor and vendor.get('status') == 'Active':
            st.success(f"Welcome, {vendor.get('vendor_name')}!")
        else:
            st.error("Account not found, inactive, or pending approval.")
