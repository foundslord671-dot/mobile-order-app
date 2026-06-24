import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

# 1. SETUP CONNECTION
@st.cache_resource
def get_sheets_connection():
    try:
        # This looks for the [gcp_service_account] section in your Streamlit Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# 2. INITIALIZE CLIENT
client = get_sheets_connection()

# 3. UI - VENDORSPACE LOGIN PAGE
st.title("VendorSpace")
st.write("Enter business email")

user_email = st.text_input("Email", key="email_input")
login_button = st.button("Login")

# 4. LOGIN LOGIC
if login_button:
    if client:
        try:
            # Replace 'Your_Sheet_Name' with your actual Google Sheet name
            # The service account email MUST be added as an Editor to that sheet!
            sh = client.open("Your_Sheet_Name") 
            worksheet = sh.sheet1
            
            # Basic check to see if email exists in column A
            email_list = worksheet.col_values(1)
            if user_email in email_list:
                st.success("Login Successful!")
            else:
                st.error("Email not found. Please check your credentials.")
                
        except Exception as e:
            st.error(f"Error accessing sheet: {e}")
    else:
        st.error("Could not establish connection to Google Sheets. Check your secrets.")
