import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURATION ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

# --- OPTIMIZED FUNCTIONS ---
# Cache the registry for 5 minutes (300 seconds) to prevent API rate limiting
@st.cache_data(ttl=300)
def get_master_registry():
    client = get_gspread_client()
    return client.open("Master_Registry").sheet1.get_all_records()

def register_vendor(name, email, sheet_id):
    client = get_gspread_client()
    registry_sheet = client.open("Master_Registry").sheet1
    registry_sheet.append_row([name, email, sheet_id, "Pending"])

def authenticate_vendor(email):
    registry = get_master_registry()
    return next((v for v in registry if v['email'] == email), None)

# --- APP INTERFACE ---
st.set_page_config(page_title="VendorSpace SaaS", layout="wide")
st.title("🚀 VendorSpace Platform")

menu = st.sidebar.radio("Navigation", ["Login", "Register as Vendor", "Admin"])

if menu == "Login":
    st.subheader("Vendor Portal Login")
    email_input = st.text_input("Enter your business email")
    if st.button("Login"):
        vendor = authenticate_vendor(email_input)
        if vendor and vendor['status'] == 'Active':
            st.session_state['vendor'] = vendor
            st.rerun()
        else:
            st.error("Account pending or not found. Contact admin.")

    if 'vendor' in st.session_state:
        v = st.session_state['vendor']
        st.success(f"Welcome {v['vendor_name']}!")
        # Fetching private data
        client = get_gspread_client()
        data = client.open_by_key(v['sheet_id']).sheet1.get_all_records()
        st.dataframe(pd.DataFrame(data))

elif menu == "Register as Vendor":
    st.subheader("Join VendorSpace")
    with st.form("signup"):
        name = st.text_input("Business Name")
        email = st.text_input("Work Email")
        sid = st.text_input("Your Google Sheet ID")
        if st.form_submit_button("Submit Application"):
            register_vendor(name, email, sid)
            # Clear cache so admin sees new user immediately
            st.cache_data.clear()
            st.success("Application sent! Awaiting admin approval.")

elif menu == "Admin":
    admin_pass = st.text_input("Admin Password", type="password")
    if admin_pass == st.secrets.get("ADMIN_PASSWORD"):
        st.write("### All Pending Applications")
        registry = get_master_registry()
        st.dataframe(pd.DataFrame(registry))
