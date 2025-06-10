# app.py
import streamlit as st
from organizeData import (
    database_setup,
    parse_row_and_insert_from_openclock,
    query_hours_entries_openclock,
    insert_user,
    create_db
)
from setup import (
    setup_driver,
    login_to_self_service,
    extract_time_from_self_service_and_select_period
)
from extract_time import select_range_dates, is_data_up_to_date

from datetime import datetime, timedelta
import time
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By

# ─── Streamlit UI ──────────────────────────────────────────────────────────────

st.title("Time Sheet Automation")

# Sidebar for credentials
with st.sidebar:
    st.header("Configuration")
    st.subheader("Username")
    username = st.text_input(
        "Username", value=st.session_state.get("username", "")
    )
    st.subheader("OpenClock Password")
    openclock_password = st.text_input(
        "OpenClock Password",
        type="password",
        value=st.session_state.get("openclock_password", "")
    )
    st.subheader("Self-Service Password")
    selfservice_password = st.text_input(
        "Self-Service Password",
        type="password",
        value=st.session_state.get("selfservice_password", "")
    )

    # Remember in session
    if username:
        st.session_state.username = username
    if openclock_password:
        st.session_state.openclock_password = openclock_password
    if selfservice_password:
        st.session_state.selfservice_password = selfservice_password

# Main pane: Data Extraction
st.header("Data Extraction")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date", value=datetime.now() - timedelta(days=30)
    )
with col2:
    end_date = st.date_input("End Date", value=datetime.now())

start_str = start_date.strftime("%m/%d/%Y")
end_str   = end_date.strftime("%m/%d/%Y")

if st.button("Extract Data from OpenClock"):
    if not username or not openclock_password:
        st.error("Enter username & OpenClock password above.")
    else:
        with st.spinner("Fetching OpenClock data…"):
            try:
                db = database_setup()
                create_db()

                # ensure user exists
                cur = db.cursor()
                cur.execute(
                    "SELECT id FROM users WHERE username = ?", (username,)
                )
                if not cur.fetchone():
                    insert_user(db, username, username, openclock_password)

                res = select_range_dates(
                    username, openclock_password, start_str, end_str
                )
                if res["data"]:
                    for row in res["data"]:
                        parse_row_and_insert_from_openclock(db, username, row)
                    st.success(f"Stored data from {res['start_date']} to {res['end_date']}")
                else:
                    st.warning("No OpenClock data for that range.")
            except Exception as e:
                st.error(f"Error: {e}")

# Self-Service Time Sheet Entry
st.header("Self-Service Time Sheet Entry")

# Keep one driver alive
if "driver" not in st.session_state:
    st.session_state.driver = None

if st.button("Close Browser"):
    if st.session_state.driver:
        try:
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.success("Browser closed.")
        except Exception as e:
            st.error(f"Error closing browser: {e}")

if st.button("Enter Time Sheet"):
    if not username or not selfservice_password:
        st.error("Enter username & Self-Service password above.")
    else:
        with st.spinner("Processing…"):
            try:
                drv = st.session_state.driver
                # init or refresh driver
                if drv is None:
                    drv = setup_driver()
                else:
                    try:
                        drv.current_url
                    except:
                        drv.quit()
                        drv = setup_driver()
                st.session_state.driver = drv

                # Kick off the flow
                result = extract_time_from_self_service_and_select_period(
                    drv, username, selfservice_password
                )
                if result:
                    st.success("Time entries processed!")
                else:
                    st.error("Failed to process time entries.")
            except Exception as e:
                st.error(f"Error: {e}")
                if st.session_state.driver:
                    try:
                        st.session_state.driver.quit()
                    except:
                        pass
                    st.session_state.driver = None

# Data status
st.header("Data Status")
if is_data_up_to_date():
    st.success("✅ Your data is up to date")
else:
    st.warning("⚠️ Your data needs to be updated")




    