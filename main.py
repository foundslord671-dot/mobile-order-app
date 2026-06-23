import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 1. SECURE AUTHENTICATION ENGINE
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Securely reads credentials from Streamlit Secrets (DO NOT use open() anymore)
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

# 2. CONNECT TO SHEET USING YOUR UNIQUE ID
SPREADSHEET_ID = "17f4PaRR5CTGqQ1X6MMEZ2um0N6YXtKWTKFR6Wjt5pGk"

try:
    client = get_gspread_client()
    workbook = client.open_by_key(SPREADSHEET_ID)
    master_sheet = workbook.get_worksheet(0)
except Exception as e:
    st.error(f"Connection Failed: {e}")
    st.stop()

# 3. INTERFACE
st.title("🚀 VendorSpace: Automated DM-Free Ordering")
app_mode = st.tabs(["🛒 Shop & Order", "🏬 Vendor Registration"])

# VENDOR REGISTRATION
with app_mode[1]:
    st.header("Register Your Business")
    raw_vendor = st.text_input("Business Name:", key="reg_name").strip()
    new_vendor = raw_vendor.replace(" ", "_")
    new_pin = st.text_input("Admin PIN:", type="password", key="reg_pin")
    new_bank = st.text_area("Bank Details:", key="reg_bank")
    
    if st.button("Create My Shop"):
        if raw_vendor and new_pin and new_bank:
            master_sheet.append_row([new_vendor, new_pin, new_bank])
            try:
                new_ws = workbook.add_worksheet(title=new_vendor, rows="1000", cols="6")
                new_ws.append_row(["Customer Name", "Phone", "Address", "Items", "Amount", "Reference"])
                st.success("Shop Created!")
            except Exception as e:
                st.error(f"Error creating shop: {e}")
        else:
            st.error("All fields required.")

# CLIENT CHECKOUT
with app_mode[0]:
    records = master_sheet.get_all_records()
    active_vendors = [r["Vendor Name"] for r in records if r.get("Vendor Name")]
    
    if not active_vendors:
        st.info("No shops registered yet.")
    else:
        chosen_display = st.selectbox("Select Shop:", ["--"] + [v.replace("_", " ") for v in active_vendors])
        if chosen_display != "--":
            chosen_store = chosen_display.replace(" ", "_")
            vendor_data = next((item for item in records if item["Vendor Name"] == chosen_store), None)
            
            if vendor_data:
                st.info(f"Transfer to: {vendor_data['Bank Account Details']}")
                
                c_name = st.text_input("Name:")
                c_phone = st.text_input("Phone:")
                c_items = st.text_input("Items:")
                c_cost = st.text_input("Amount:")
                c_addr = st.text_area("Address:")
                c_ref = st.text_input("Payment Reference/Sender Name:")
                
                if st.button("Submit Order"):
                    try:
                        ws = workbook.worksheet(chosen_store)
                        ws.append_row([c_name, c_phone, c_addr, c_items, c_cost, c_ref])
                        st.success("Order Sent!")
                    except Exception as e:
                        st.error(f"Error: {e}")
