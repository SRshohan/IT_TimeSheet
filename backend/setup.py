from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import string
from organizeData import query_hours_entries_openclock, database_setup
import streamlit as st
from organizeData import insert_gcal_data

load_dotenv()

# This is the database connection
db = database_setup()
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

# This function is used to convert the time to the required format
def convert_time_24_to_12_format(time):
    time_obj = datetime.strptime(time, "%H:%M:%S") # Format: 10:00:00
    formatted_time = time_obj.strftime("%I:%M %p") # Format: 10:00 AM
    return formatted_time.split()

# Convert the date to the required format
def convert_date_to_required_format(date):
    date_obj = datetime.strptime(date, "%Y-%m-%d") # Format: 2025-05-26

    # Convert to required format
    formatted_date = date_obj.strftime("%A\n%b %d, %Y") # Format: Monday\nMay 26, 2025
    print(formatted_date)

# This function is used to convert the date to a datetime object
def convert_to_date(date):
    try:
        date = date.split("\n")
        date = date[-1].strip()  # e.g., "Jun 02, 2025"
        date_obj = datetime.strptime(date, "%b %d, %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")  # Format: 2025-06-02
        return (formatted_date, True)
    except ValueError:
        return (date, False)

# This function is used to enter the hours into the Each Day time sheet
def convert_time_24_to_12_format(time_str):
    """Converts '18:00:00' to ('06:00', 'PM')"""
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    return time_obj.strftime("%I:%M"), time_obj.strftime("%p")

def enter_all_hours(driver, shifts):
    """
    shifts: a list of tuples, e.g.,
    [('10:00:00', '12:00:00'), ('13:00:00', '15:00:00')] — must be 24-hour format with seconds
    """
    try:
        for i, (start_time_24, end_time_24) in enumerate(shifts):
            row_index = i + 2  # since HTML rows start at 2nd tr (1-based index)
            
            # Convert time
            start_time, clck_in_am_pm = convert_time_24_to_12_format(start_time_24)
            end_time, clck_out_am_pm = convert_time_24_to_12_format(end_time_24)

            # Time In
            timein_input_xpath = f'/html/body/div[3]/form/table[2]/tbody/tr[{row_index}]/td[2]/input'
            driver.find_element(By.XPATH, timein_input_xpath).send_keys(start_time)

            # Time In AM/PM dropdown
            timein_dropdown_xpath = f'/html/body/div[3]/form/table[2]/tbody/tr[{row_index}]/td[3]/select'
            Select(driver.find_element(By.XPATH, timein_dropdown_xpath)).select_by_visible_text(clck_in_am_pm)

            # Time Out
            timeout_input_xpath = f'/html/body/div[3]/form/table[2]/tbody/tr[{row_index}]/td[4]/input'
            driver.find_element(By.XPATH, timeout_input_xpath).send_keys(end_time)

            # Time Out AM/PM dropdown
            timeout_dropdown_xpath = f'/html/body/div[3]/form/table[2]/tbody/tr[{row_index}]/td[5]/select'
            Select(driver.find_element(By.XPATH, timeout_dropdown_xpath)).select_by_visible_text(clck_out_am_pm)

        # Save and go back once after all entries
        wait = WebDriverWait(driver, 10)
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[2]/td/input[2]")))
        save_button.click()
        
        # Wait for the page to load after saving
        wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[1]/td/input[1]")))
        back_button = driver.find_element(By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[1]/td/input[1]")
        back_button.click()
        
        # Wait for the main page to load
        wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td")))
        return True
    except Exception as e:
        print("Error in enter_all_hours:", e)
        return False

# This function is used to go to the next and previous page of the time sheet
def nextAndPrevious(driver):
    try:
        next_button = driver.find_element(By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td/form/table[2]/tbody/tr/td[6]/input")
        value = next_button.get_attribute("value")
        print(value)
        next_button.click()
        return value
    except Exception as e:
        print("Error at Next and Previous:", e)
        return None

def time_entries_each_day_to_time_sheet(driver):
    date_list = []
    try:
        # Get the selected period from session state
        selected_period = st.session_state.time_periods[st.session_state.dropdown_options.index(st.session_state.time_period_select)]
        selected_start_date = selected_period['start_date']
        selected_end_date = selected_period['end_date']
        
        print(f"Processing time entries for period: {selected_start_date.strftime('%Y-%m-%d')} to {selected_end_date.strftime('%Y-%m-%d')}")
        
        # Create a new database connection for this thread
        db = database_setup()
        
        while True:  # Keep looping until we reach the last page
            wait = WebDriverWait(driver, 10)

            # Wait for table to be ready
            table = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td")))
            rows = table.find_elements(By.TAG_NAME, "tr")

            if len(rows) < 2:
                print("No time entries found")
                return [], False

            header_cells = rows[0].find_elements(By.TAG_NAME, "td")
            action_cells = rows[1].find_elements(By.TAG_NAME, "td")

            for index, cell in enumerate(header_cells):
                text = cell.text.strip()
                date, is_date = convert_to_date(text)

                if is_date:
                        # Convert string date to datetime for comparison
                        current_date = datetime.strptime(date, "%Y-%m-%d")
                        
                        # Only process dates within the selected period
                    
                        date_list.append((date, index))

                        insert_gcal_data(db, username, current_date)
                        
                        # Query the database for this date
                        time_entry = query_hours_entries_openclock(db, username, date)
                        print(f"Time entries for {date}: {time_entry}")
                        
                        if not time_entry or len(time_entry) == 0:
                            print(f"No time entries found for {date}, skipping...")
                            continue

                        # Process the time entries and create shifts list
                        shifts = []
                        for entry in time_entry:
                            if isinstance(entry[5], str):
                                shifts.append((entry[3], entry[4]))
                                print(f"Added GCal shift for {date}")
                            elif entry[5] <= 0:
                                print(f"Time difference is less than 15 minutes for {date}, skipping...")
                                continue
                            else:
                                shifts.append((entry[3], entry[4]))
                                print(f"Added shift for {date}: {entry[3]} to {entry[4]}")
                        
                        if shifts and len(shifts) > 0:
                            print(f"Processing {len(shifts)} shifts for {date}")
                            if action_cells[index].text == "Enter Hours":
                                enter_hours_link = action_cells[index].find_element(By.PARTIAL_LINK_TEXT, "Enter Hours")
                                enter_hours_link.click()
                                
                                # Wait for the new page to load
                                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/form/table[2]/tbody/tr[2]/td[2]/input")))
                                
                                print(f"Entering hours for {date}")
                                result = enter_all_hours(driver, shifts)
                                print(f"Result for {date}: {result}")
                            else:
                                print(f"Action cell text for {date}: {action_cells[index].text}")
                        else:
                            print(f"No valid shifts found for {date}")
                    

            # Use the nextAndPrevious function for navigation
            button_text = nextAndPrevious(driver)
            if button_text == "Previous":
                print("Reached the last page, stopping...")
                break
            else:
                print("Moving to next page...")
                # Wait for the new page to load
                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td")))

        print("Final date list:", date_list)
        return date_list, True

    except Exception as e:
        print("Error in time_entries_each_day_to_time_sheet:", e)
        return [], False
    finally:
        # Close the database connection
        if 'db' in locals():
            db.close()


# This function is used to parse the line of the time period
def parse_line(line):
    # Example: "May 11, 2025 to May 24, 2025 In Progress"
    match = re.match(r"([A-Za-z]{3,9} \d{1,2}, \d{4}) to ([A-Za-z]{3,9} \d{1,2}, \d{4}) (.+)", line)
    if not match:
        raise ValueError(f"Line format incorrect: {line}")
    start_str, end_str, status = match.groups()
    start_date = datetime.strptime(start_str.strip(), "%b %d, %Y")
    end_date = datetime.strptime(end_str.strip(), "%b %d, %Y")
    return {
        "start_date": start_date,
        "end_date": end_date,
        "status": status
    }

# This function is used to setup the driver
def setup_driver():
    # Get the path of the current file
    path = "../chromedriver-mac-arm64/chromedriver"

    if not os.path.exists(path):
        raise Exception(f"ChromeDriver not found at path: {path}. Please ensure the ChromeDriver is installed in the correct location.")

    service = Service(path)
    options = Options()
    # Add options to prevent multiple instances
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    # Add a unique user data directory to prevent conflicts
    options.add_argument(f"--user-data-dir=./chrome_profile_{int(time.time())}")
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        raise Exception(f"Failed to create Chrome driver: {str(e)}")


# This function is used to login to the self service website
def login_to_self_service(driver, username, password):
    try:
        # Check if we're already logged in
        if "selfservice.manhattan.edu" in driver.current_url:
            st.info("Already logged in, proceeding to time sheet...")
        else:
            driver.get("https://selfservice.manhattan.edu/")

            # Click the "Sign In Via JasperNet" link
            driver.find_element(By.ID, "read-link-0").click()
            
            # Now type the username and password
            driver.find_element(By.ID, "username").send_keys(username)
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.NAME, "_eventId_proceed").click()

            wait = WebDriverWait(driver, 20)
            duo_header = wait.until(EC.presence_of_element_located((By.ID, "header-text")))

            if duo_header.text == "Enter code in Duo Mobile":
                element = driver.find_element(By.CLASS_NAME, "verification-code")
                code = element.text
                st.info(f"Please enter this code in Duo Mobile: {code}")
                
                # Wait for user to enter the code
                while True:
                    try:
                        trust_screen = driver.find_element(By.ID, "trust-this-browser-label")
                        if trust_screen.text == "Is this your device?":
                            driver.find_element(By.ID, "trust-browser-button").click()
                            time.sleep(5)
                            break
                    except:
                        time.sleep(1)
                        continue

        # Navigate to time sheet
        st.info("Navigating to time sheet...")
        menu_button = driver.find_element(By.ID, "bannerMenu")
        menu_button.click()
        time.sleep(5)
        
        banner_text = driver.find_element(By.XPATH, '//*[@id="list_Banner"]/div/div[1]/span')
        banner_text.click()
        time.sleep(5)
        
        financial_aid = driver.find_element(By.XPATH, '//*[@id="list_Banner_Financial Aid"]/div/div[1]/span')
        financial_aid.click()
        time.sleep(5)
        
        student_employment = driver.find_element(By.XPATH, '//*[@id="list_Banner_Financial Aid_Student Employment Menu"]/div/div[1]/span')
        student_employment.click()
        time.sleep(5)
        
        time_sheet = driver.find_element(By.XPATH, '//*[@id="list_Banner_Financial Aid_Student Employment Menu_Enter Time Sheet"]/a/div/div/span')
        time_sheet.click()
        time.sleep(5)
        
        st.info("Loading time periods...")
        select_time_period = driver.find_element(By.XPATH, '//*[@id="period_1_id"]')
        raw_data = select_time_period.text.split('\n')
        
        # Parse periods from the self-service website
        structured_data = []
        for line in raw_data:
            if line.strip():
                try:
                    period = parse_line(line)
                    structured_data.append(period)
                except ValueError:
                    continue
        
        if not structured_data:
            st.error("No available time periods found")
            return None
        
        # Store the driver in session state for use in extract_time_from_self_service_and_select_period
        st.session_state.driver = driver
        
        return structured_data
            
    except Exception as e:
        st.error(f"Error during login: {str(e)}")
        return None


def extract_time_from_self_service_and_select_period(driver):
    if 'driver' not in st.session_state:
        st.error("No active browser session found")
        return None
        
    driver = st.session_state.driver
    
    try:
        # Create dropdown options with status indicators for Streamlit UI
        dropdown_options = []
        for p in st.session_state.time_periods:
            status_indicator = "✅" if p['status'].lower() == 'completed' else "⏳"
            dropdown_options.append(
                f"{status_indicator} {p['start_date'].strftime('%b %d, %Y')} to {p['end_date'].strftime('%b %d, %Y')} - {p['status']}"
            )
        
        # Store dropdown options in session state
        st.session_state.dropdown_options = dropdown_options
        
        # Show dropdown in Streamlit
        selected_option = st.selectbox(
            "Select Time Period",
            options=dropdown_options,
            key='time_period_select'
        )
        
        # Get the selected period
        selected_index = dropdown_options.index(selected_option)
        selected_period = st.session_state.time_periods[selected_index]
        
        # Wait for the dropdown to be present
        wait = WebDriverWait(driver, 10)
        dropdown = wait.until(EC.presence_of_element_located((By.ID, "period_1_id")))
        select = Select(dropdown)
        
        # Get all options from the self-service dropdown
        available_periods = []
        for option in select.options:
            if option.text.strip():
                try:
                    period = parse_line(option.text)
                    available_periods.append((option.text, period))
                except ValueError:
                    continue
        
        # Find the matching period in the self-service dropdown
        matching_option = None
        for option_text, period in available_periods:
            if (period['start_date'] == selected_period['start_date'] and 
                period['end_date'] == selected_period['end_date'] and 
                period['status'] == selected_period['status']):
                matching_option = option_text
                break
        
        if matching_option is None:
            st.error("Could not find matching period in self-service dropdown")
            return None
        
        # Select the period in the self-service dropdown using the exact text from the dropdown
        select.select_by_visible_text(matching_option)
        print(f"Selected period in self-service: {matching_option}")
        time.sleep(2)
        
        # Click the time sheet button
        time_sheet_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/form/table[2]/tbody/tr/td/input')))
        time_sheet_button.click()
        print("Clicked time sheet button")
        time.sleep(2)
        
        # Process time entries - this will handle all navigation internally
        date_list, success = time_entries_each_day_to_time_sheet(driver)
        if success:
            st.success("Time entries processed successfully!")
        else:
            st.warning("No time entries found or processed.")
        
        print("Time period selection and processing completed")
        return True
        
    except Exception as e:
        st.error(f"Error during time period selection: {str(e)}")
        return None



if __name__ == "__main__":
    driver = setup_driver()
    # 1. Get all dates in the time period
    selected_period = extract_time_from_self_service_and_select_period(driver)
    print(selected_period)
    







