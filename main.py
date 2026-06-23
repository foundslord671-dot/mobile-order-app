import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(
    page_title="VendorSpace SaaS", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def get_master_registry():
    # Using your specific Sheet ID to ensure the connection works flawlessly
    MASTER_SHEET_ID = "1I0672UQXrjuFRBK_dAgHWN5gnqQoc-8sT0iPyuQnLeE"
    client = get_gspread_client()
    return client.open_by_key(MASTER_SHEET_ID).sheet1.get_all_records()

def register_vendor(name, email, sheet_id):
    client = get_gspread_client()
    MASTER_SHEET_ID = "1I0672UQXrjuFRBK_dAgHWN5gnqQoc-8sT0iPyuQnLeE"
    registry_sheet = client.open_by_key(MASTER_SHEET_ID).sheet1
    registry_sheet.append_row([name, email, sheet_id, "Pending"])

def authenticate_vendor(email):
    registry = get_master_registry()
    return next((v for v in registry if v['email'] == email), None)

# --- APP INTERFACE ---
st.title("🚀 VendorSpace")

# Navigation
menu = st.sidebar.radio("Menu", ["Login", "Register as Vendor", "Admin"])

if menu == "Login":
    st.subheader("Vendor Portal")
    email_input = st.text_input("Enter business email")
    
    if st.button("Login"):
        vendor = authenticate_vendor(email_input)
        if vendor and vendor['status'] == 'Active':
            st.session_state['vendor'] = vendor
            st.rerun()
        else:
            st.error("Account pending or not found. Please contact admin.")

    if 'vendor' in st.session_state:
        v = st.session_state['vendor']
        st.success(f"Welcome, {v['vendor_name']}!")
        client = get_gspread_client()
        # Fetching vendor-specific data
        data = client.open_by_key(v['sheet_id']).sheet1.get_all_records()
        st.dataframe(pd.DataFrame(data), use_container_width=True)

elif menu == "Register as Vendor":
    st.subheader("Join VendorSpace")
    with st.form("signup"):
        name = st.text_input("Business Name")
        email = st.text_input("Work Email")
        sid = st.text_input("Google Sheet ID")
        if st.form_submit_button("Submit Application"):
            register_vendor(name, email, sid)
            st.cache_data.clear() # Refresh registry for admin
            st.success("Application sent! Awaiting admin approval.")

elif menu == "Admin":
    admin_pass = st.text_input("Admin Password", type="password")
    if admin_pass == st.secrets.get("ADMIN_PASSWORD"):
        st.write("### Master Registry")
        registry = get_master_registry()
        st.dataframe(pd.DataFrame(registry), use_container_width=True)
