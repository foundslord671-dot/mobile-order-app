import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 1. SECURE AUTHENTICATION ENGINE
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # This reads the dictionary from the Streamlit Secrets TOML
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

# 2. CONNECT TO SHEET
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
            # Check if vendor already exists to prevent duplicate worksheets
            records = master_sheet.get_all_records()
            if any(r["Vendor Name"] == new_vendor for r in records):
                st.warning("This shop name is already taken!")
            else:
                master_sheet.append_row([new_vendor, new_pin, new_bank])
                try:
                    new_ws = workbook.add_worksheet(title=new_vendor, rows="1000", cols="6")
                    new_ws.append_row(["Customer Name", "Phone", "Address", "Items", "Amount", "Reference"])
                    st.success(f"Shop '{raw_vendor}' Created Successfully!")
                except Exception as e:
                    st.error(f"Error creating shop worksheet: {e}")
        else:
            st.error("All fields are required.")

# CLIENT CHECKOUT
with app_mode[0]:
    records = master_sheet.get_all_records()
    active_vendors = [r["Vendor Name"] for r in records if r.get("Vendor Name")]
    
    if not active_vendors:
        st.info("No shops registered yet. Please register one in the 'Vendor Registration' tab.")
    else:
        chosen_display = st.selectbox("Select Shop:", ["--"] + [v.replace("_", " ") for v in active_vendors])
        if chosen_display != "--":
            chosen_store = chosen_display.replace(" ", "_")
            vendor_data = next((item for item in records if item["Vendor Name"] == chosen_store), None)
            
            if vendor_data:
                st.info(f"**Transfer to:** {vendor_data['Bank Account Details']}")
                
                with st.form("order_form"):
                    c_name = st.text_input("Full Name:")
                    c_phone = st.text_input("Phone Number:")
                    c_items = st.text_input("Items Ordered:")
                    c_cost = st.text_input("Total Amount:")
                    c_addr = st.text_area("Delivery Address:")
                    c_ref = st.text_input("Payment Reference/Sender Name:")
                    
                    submit = st.form_submit_button("Submit Order")
                    
                    if submit:
                        if c_name and c_items and c_ref:
                            try:
                                ws = workbook.worksheet(chosen_store)
                                ws.append_row([c_name, c_phone, c_addr, c_items, c_cost, c_ref])
                                st.success("Order Sent Successfully!")
                            except Exception as e:
                                st.error(f"Error submitting order: {e}")
                        else:
                            st.warning("Please fill in the required order fields.")
