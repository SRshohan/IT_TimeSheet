from organizeData import database_setup, parse_row_and_insert_from_openclock, query_hours_entries_openclock, insert_user, create_db
from setup import setup_driver, login_to_self_service, extract_time_from_self_service_and_select_period
from extract_time import select_range_dates, is_data_up_to_date
import streamlit as st
from datetime import datetime, timedelta
from selenium.webdriver.support.select import Select
import time
from selenium.webdriver.common.by import By

# Streamlit UI
st.title("Time Sheet Automation")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Username (shared between OpenClock and Self-Service)
    st.subheader("Username")
    username = st.text_input("Username", value=st.session_state.get('username', ''))
    
    # Passwords
    st.subheader("Passwords")
    openclock_password = st.text_input("OpenClock Password", type="password", value=st.session_state.get('openclock_password', ''))
    selfservice_password = st.text_input("Self-Service Password", type="password", value=st.session_state.get('selfservice_password', ''))
    
    # Save credentials to session state
    if username:
        st.session_state.username = username
    if openclock_password:
        st.session_state.openclock_password = openclock_password
    if selfservice_password:
        st.session_state.selfservice_password = selfservice_password

# Main content
st.header("Data Extraction")

# Date range selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("End Date", value=datetime.now())

# Format dates for OpenClock
start_date_str = start_date.strftime("%m/%d/%Y")
end_date_str = end_date.strftime("%m/%d/%Y")

# Manual extraction button
if st.button("Extract Data from OpenClock"):
    if not username or not openclock_password:
        st.error("Please enter your username and OpenClock password in the sidebar")
    else:
        with st.spinner("Extracting data from OpenClock..."):
            try:
                # Initialize database
                db = database_setup()
                create_db()
                
                # Check if user exists, if not create them
                cursor = db.cursor()
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                if not cursor.fetchone():
                    st.info(f"Creating new user: {username}")
                    insert_user(db, username, username, openclock_password)
                
                result = select_range_dates(username, openclock_password, start_date_str, end_date_str)
                if result['data']:
                    # Parse and insert data into SQLite
                    for row in result['data']:
                        parse_row_and_insert_from_openclock(db, username, row)
                    st.success(f"Data extracted and stored successfully from {result['start_date']} to {result['end_date']}")
                else:
                    st.warning("No data found for the selected date range")
            except Exception as e:
                st.error(f"Error extracting data: {str(e)}")

# Self-Service Time Sheet Entry
st.header("Self-Service Time Sheet Entry")

# Initialize driver in session state if not exists
if 'driver' not in st.session_state:
    st.session_state.driver = None

# Add a cleanup button at the top of the page
if st.button("Close Browser"):
    if st.session_state.driver:
        try:
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.success("Browser closed successfully")
        except Exception as e:
            st.error(f"Error closing browser: {str(e)}")
            st.session_state.driver = None

if st.button("Enter Time Sheet"):
    if not username or not selfservice_password:
        st.error("Please enter your username and Self-Service password in the sidebar")
    else:
        with st.spinner("Setting up browser..."):
            try:
                # Only create new driver if one doesn't exist
                if st.session_state.driver is None:
                    st.session_state.driver = setup_driver()
                else:
                    try:
                        # Test if the existing driver is still responsive
                        st.session_state.driver.current_url
                    except:
                        # If not responsive, create a new one
                        st.session_state.driver.quit()
                        st.session_state.driver = setup_driver()
                
                # First login and get the structured data
                structured_data = login_to_self_service(st.session_state.driver, username, selfservice_password)
                
                if structured_data is None:
                    st.error("Failed to load time periods")
                else:
                    # Store the periods in session state
                    st.session_state.time_periods = structured_data
                    
                    # Now show the dropdown and process time entries
                    result = extract_time_from_self_service_and_select_period(st.session_state.driver)
                    if result:
                        st.success("Time entries processed successfully!")
                    else:
                        st.error("Failed to process time entries")
                
            except Exception as e:
                st.error(f"Error during time sheet entry: {str(e)}")
                # Clean up driver on error
                if st.session_state.driver:
                    try:
                        st.session_state.driver.quit()
                    except:
                        pass
                    st.session_state.driver = None

# Data Status
st.header("Data Status")
if is_data_up_to_date():
    st.success("✅ Your data is up to date")
else:
    st.warning("⚠️ Your data needs to be updated")



    