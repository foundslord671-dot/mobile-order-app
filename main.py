import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import random

# 1. Secure connection to Google Sheets using Streamlit Secrets
@st.cache_resource
def connect_to_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    return client

# Initialize client and open spreadsheet
try:
    client = connect_to_sheets()
    sheet = client.open("Mobile Vendor DB")
    inventory_sheet = sheet.worksheet("Inventory")
    orders_sheet = sheet.worksheet("Orders")
except Exception as e:
    st.error("⚠️ System connecting to database... Setup required.")
    st.stop()

# 2. Fetch inventory data from the Google Sheet dynamically
try:
    inventory_data = inventory_sheet.get_all_records()
    
    available_items = {}
    for row in inventory_data:
        if int(row['Stock']) > 0:
            item_label = f"{row['Item Name']} (₦{int(row['Price']):,})"
            available_items[item_label] = {
                "name": row['Item Name'],
                "price": int(row['Price'])
            }
    
    item_options = ["Select an item..."] + list(available_items.keys())
except Exception as e:
    st.error("Could not load inventory columns. Check your Google Sheet headers.")
    st.stop()

# 3. Mobile Layout Interface Setup
st.set_page_config(page_title="Mobile Checkout Counter", layout="centered")
st.title("🛍️ Fast Order Checkout")
st.write("Fill out details to order instantly. The seller will be notified.")
st.markdown("---")

# Customer details collection
st.subheader("👤 Customer Details")
customer_name = st.text_input("Full Name", placeholder="e.g., Aliyu Chinedu")
phone_number = st.text_input("WhatsApp Phone Number", placeholder="e.g., 0803XXXXXXX")
delivery_address = st.text_area("Delivery Address", placeholder="Enter full delivery location...")

# Order section selection
st.subheader("📦 Order Selection")
selected_display = st.selectbox("Choose Item", item_options)
quantity = st.number_input("Quantity", min_value=1, max_value=10, value=1)

st.markdown("---")

# 4. Processing Order Logic on Button Click
if st.button("Submit Order 🚀", use_container_width=True):
    if not customer_name or not phone_number or selected_display == "Select an item...":
        st.error("⚠️ Please fill out all required fields!")
    else:
        chosen_product = available_items[selected_display]
        total_price = chosen_product["price"] * quantity
        order_id = f"ORD-{random.randint(10000, 99999)}"
        
        new_order = [
            order_id,
            customer_name,
            phone_number,
            delivery_address,
            chosen_product["name"],
            quantity,
            total_price,
            "Unpaid"
        ]
        
        try:
            orders_sheet.append_row(new_order)
            st.success(f"🎉 Order Submitted Successfully, {customer_name}!")
            st.metric(label="Total Bill", value=f"₦{total_price:,}")
            st.balloons()
            
            st.info("💡 **Order Receipt Snapshot:**\n\n"
                    f"**Order ID:** {order_id}\n"
                    f"**Item:** {chosen_product['name']} x{quantity}\n"
                    f"**Delivery to:** {delivery_address}")
                    
        except Exception as e:
            st.error("Database connection timeout. Please check your credentials config.")
