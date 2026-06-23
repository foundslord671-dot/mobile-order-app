import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Database Connection Engine
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
try:
    secret_creds = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(secret_creds, scopes=scope)
    client = gspread.authorize(creds)
    workbook = client.open("mobile vendor DB")
    
    # Target the very first sheet tab dynamically
    master_sheet = workbook.get_worksheet(0) 
except Exception as e:
    st.error("Database connection failed. Please check your Streamlit Secrets.")
    st.stop()

# 2. HEALER LOOP: Auto-repair the Google Sheet layout if empty
try:
    # Try reading the first row
    first_row = master_sheet.row_values(1)
    if not first_row or "Vendor Name" not in first_row:
        # If headers are missing or blank, overwrite row 1 automatically!
        master_sheet.insert_row(["Vendor Name", "Password/PIN", "Bank Account Details"], 1)
except Exception:
    st.error("Could not write initial setup to Google Sheets. Verify permissions.")
    st.stop()

# 3. Main Portal Interface Layout
st.title("🚀 VendorSpace: Automated DM-Free Ordering")
st.write("The platform built for online vendors to receive clear orders without messy chats.")

# Create navigation tabs at the top for Users vs Business Owners
app_mode = st.tabs(["🛒 Shop & Order", "🏬 Vendor Registration"])

# -------------------------------------------------------------
# TAB 1: VENDOR REGISTRATION (Self-Service Onboarding)
# -------------------------------------------------------------
with app_mode[1]:
    st.header("Register Your Online Business")
    st.write("Fill this out to instantly launch your automated digital order page!")
    
    new_vendor = st.text_input("Business/Shop Name:", key="reg_name").strip().replace(" ", "_")
    new_pin = st.text_input("Create Account Admin PIN (4 Digits):", type="password", key="reg_pin")
    new_bank = st.text_area("Your Bank Details (e.g., OPay - 1234567890 - Name):", key="reg_bank")
    
    if st.button("Create My Automated Shop Link"):
        if new_vendor and new_pin and new_bank:
            existing_records = master_sheet.get_all_records()
            taken_names = [row.get("Vendor Name") for row in existing_records if row.get("Vendor Name")]
            
            if new_vendor in taken_names:
                st.error("❌ This Business Name is already registered.")
            else:
                # Log them into the master folder
                master_sheet.append_row([new_vendor, new_pin, new_bank])
                
                # Automatically create their custom database workspace tab
                try:
                    new_ws = workbook.add_worksheet(title=new_vendor, rows="1000", cols="10")
                    new_ws.append_row(["Customer Name", "Phone Number", "Delivery Address/Info", "Items Ordered", "Amount Paid", "Receipt Status"])
                    st.success(f"🎉 Success! '{new_vendor.replace('_',' ')}' is now live. Refresh the shop page to see it!")
                except Exception:
                    st.error("Shop registered, but workspace creation timed out. Check your Google Sheet to see if the tab was created!")
        else:
            st.error("❌ All registration fields are required.")

# -------------------------------------------------------------
# TAB 0: CLIENT CHECKOUT SYSTEM (The Storefront Interface)
# -------------------------------------------------------------
with app_mode[0]:
    try:
        records = master_sheet.get_all_records()
        active_vendors = [row.get("Vendor Name") for row in records if row.get("Vendor Name")]
    except Exception:
        active_vendors = []

    if not active_vendors:
        st.info("💡 No stores are registered yet. Click the 'Vendor Registration' tab to set up the first store!")
    else:
        chosen_store = st.selectbox("🏬 Choose the store you are buying from:", ["-- Select Shop --"] + active_vendors)
        
        if chosen_store != "-- Select Shop --":
            current_vendor_data = next(item for item in records if item.get("Vendor Name") == chosen_store)
            active_payment_info = current_vendor_data.get("Bank Account Details", "No bank details listed.")
            
            st.subheader(f"🛒 Shopping at: {chosen_store.replace('_', ' ')}")
            st.info(f"📌 **Payment Instructions:**\n\nTransfer your total order value to:\n`{active_payment_info}`")
            st.markdown("---")
            
            cust_name = st.text_input("Your Full Name:")
            cust_phone = st.text_input("Your Phone/WhatsApp Number:")
            cust_items = st.text_input("Items to Buy (e.g., 3GB Data, Shoes):")
            cust_cost = st.text_input("Total Bill Amount (₦):")
            cust_address = st.text_area("Your Complete Delivery Address:")
            cust_receipt = st.file_uploader("Upload Your Payment Screenshot Confirmation:", type=["png", "jpg", "jpeg"])
            
            st.markdown("---")
            
            if st.button("Submit My Order"):
                if cust_name and cust_phone and cust_items and cust_cost and cust_address:
                    if cust_receipt:
                        try:
                            vendor_target_sheet = workbook.worksheet(chosen_store)
                            status_str = f"Uploaded: {cust_receipt.name}"
                            
                            vendor_target_sheet.append_row([
                                cust_name, cust_phone, cust_address, cust_items, f"₦{cust_cost}", status_str
                            ])
                            st.success(f"🎉 Order sent successfully to {chosen_store.replace('_',' ')}!")
                        except gspread.exceptions.WorksheetNotFound:
                            st.error("Error: This vendor's order tab was not found.")
                    else:
                        st.warning("⚠️ Please attach your payment transfer screenshot.")
                else:
                    st.error("❌ Please fill out all fields.")
