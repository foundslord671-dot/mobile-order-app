import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# -------------------------------------------------------------
# 1. OPTIMIZED DATABASE CONNECTION ENGINE (CACHED)
# -------------------------------------------------------------
# This prevents Streamlit from logging into Google on every click,
# protecting you from hitting API rate limits and getting banned.
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Directly reading the secrets structure as a native dictionary
        secret_creds = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(secret_creds, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Database authentication setup failed: {e}")
        return None

client = get_gspread_client()

if client is None:
    st.error("Could not establish cloud pipeline. Check your Streamlit Dashboard Secrets.")
    st.stop()

try:
    workbook = client.open("mobile vendor DB")
    master_sheet = workbook.get_worksheet(0) 
except Exception as e:
    st.error("Connected to Google, but couldn't find the spreadsheet 'mobile vendor DB'. Did you share it with your service account email?")
    st.stop()

# -------------------------------------------------------------
# 2. HEALER LOOP: Auto-repair the Master Sheet Layout
# -------------------------------------------------------------
try:
    # Safely fetch row values without throwing empty sheet exceptions
    first_row = master_sheet.row_values(1)
    if not first_row or "Vendor Name" not in first_row:
        master_sheet.insert_row(["Vendor Name", "Password/PIN", "Bank Account Details"], 1)
except Exception:
    st.error("Could not verify or write initial setup to Master Sheet. Check Editor permissions.")
    st.stop()

# -------------------------------------------------------------
# 3. MAIN PORTAL INTERFACE LAYOUT
# -------------------------------------------------------------
st.title("🚀 VendorSpace: Automated DM-Free Ordering")
st.write("The platform built for online vendors to receive clear orders without messy chats.")

# Create clean navigation tabs
app_mode = st.tabs(["🛒 Shop & Order", "🏬 Vendor Registration"])

# -------------------------------------------------------------
# TAB 1: VENDOR REGISTRATION (Self-Service Onboarding)
# -------------------------------------------------------------
with app_mode[1]:
    st.header("Register Your Online Business")
    st.write("Fill this out to instantly launch your automated digital order page!")
    
    # Force names to be unique and clean for Google Sheet tab naming conventions
    raw_vendor = st.text_input("Business/Shop Name:", key="reg_name").strip()
    new_vendor = raw_vendor.replace(" ", "_")
    new_pin = st.text_input("Create Account Admin PIN (4 Digits):", type="password", key="reg_pin")
    new_bank = st.text_area("Your Bank Details (e.g., OPay - 1234567890 - Name):", key="reg_bank")
    
    if st.button("Create My Automated Shop Link"):
        if new_vendor and new_pin and new_bank:
            existing_records = master_sheet.get_all_records()
            # Safe parsing even if fields are malformed
            taken_names = [row.get("Vendor Name") for row in existing_records if row.get("Vendor Name")]
            
            if new_vendor in taken_names:
                st.error("❌ This Business Name is already registered.")
            else:
                # Log vendor info to master sheet
                master_sheet.append_row([new_vendor, new_pin, new_bank])
                
                # Automatically spin up their custom database tab workspace
                try:
                    new_ws = workbook.add_worksheet(title=new_vendor, rows="1000", cols="6")
                    new_ws.append_row(["Customer Name", "Phone Number", "Delivery Address/Info", "Items Ordered", "Amount Paid", "Payment Reference/Sender"])
                    st.success(f"🎉 Success! '{raw_vendor}' is now live. Switch over to the shop tab to view it!")
                except Exception as e:
                    st.error(f"Shop index registered, but tab workspace creation timed out: {e}")
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
        # Create a user-friendly selector showing readable names
        display_options = ["-- Select Shop --"] + [v.replace("_", " ") for v in active_vendors]
        chosen_display = st.selectbox("🏬 Choose the store you are buying from:", display_options)
        
        if chosen_display != "-- Select Shop --":
            # Reconstruct internal tab database code key name
            chosen_store = chosen_display.replace(" ", "_")
            
            # Fetch payment metadata dynamically
            current_vendor_data = next((item for item in records if item.get("Vendor Name") == chosen_store), None)
            
            if current_vendor_data:
                active_payment_info = current_vendor_data.get("Bank Account Details", "No bank details listed.")
                
                st.subheader(f"🛒 Shopping at: {chosen_display}")
                st.info(f"📌 **Payment Instructions:**\n\nTransfer your total order value to:\n\n`{active_payment_info}`")
                st.markdown("---")
                
                cust_name = st.text_input("Your Full Name:")
                cust_phone = st.text_input("Your Phone/WhatsApp Number:")
                cust_items = st.text_input("Items to Buy (e.g., 3GB Data, Black Shoes):")
                cust_cost = st.text_input("Total Bill Amount (₦):")
                cust_address = st.text_area("Your Complete Delivery Address:")
                
                # REPLACED FILE UPLOADER CRASH: Swapped file buffer dependency for robust textual transaction audits.
                cust_audit = st.text_input("Payment Proof: Enter your Transfer Session ID / Reference Number or Sender Name:")
                
                st.markdown("---")
                
                if st.button("Submit My Order"):
                    if cust_name and cust_phone and cust_items and cust_cost and cust_address and cust_audit:
                        try:
                            # Target the specific sub-worksheet tab for the vendor
                            vendor_target_sheet = workbook.worksheet(chosen_store)
                            
                            vendor_target_sheet.append_row([
                                cust_name, cust_phone, cust_address, cust_items, f"₦{cust_cost}", cust_audit
                            ])
                            st.success(f"🎉 Order sent successfully to {chosen_display}! The vendor will process it directly.")
                        except gspread.exceptions.WorksheetNotFound:
                            st.error("Error: This vendor's workspace sheet tab was not found.")
                        except Exception as e:
                            st.error(f"Failed to submit order layout: {e}")
                    else:
                        st.error("❌ Please fill out all fields, including payment verification details.")
            else:
                st.error("Error matching store workspace data.")
