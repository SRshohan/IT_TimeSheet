# setup.py
import os
import time
import re
import string
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from organizeData import query_hours_entries_openclock, database_setup, insert_gcal_data, gcal_get_data

load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Database connection & creds
db = database_setup()

def convert_time_24_to_12_format(time_str):
    """Converts '18:00:00' → ('06:00', 'PM')."""
    t = datetime.strptime(time_str, "%H:%M:%S")
    return t.strftime("%I:%M"), t.strftime("%p")


def convert_to_date(cell_text):
    """Parses table header text like 'Mon\nJun 02, 2025' → ('2025-06-02', True)."""
    try:
        parts = cell_text.split("\n")
        raw = parts[-1].strip()
        dt = datetime.strptime(raw, "%b %d, %Y")
        return dt.strftime("%Y-%m-%d"), True
    except ValueError:
        return cell_text, False


def enter_all_hours(driver, shifts):
    """
    Given a list of (start_24h, end_24h) strings, fill in the
    "Enter Hours" form for each row.
    """
    try:
        wait = WebDriverWait(driver, 10)
        for i, (in24, out24) in enumerate(shifts):
            row = i + 2
            start, in_ampm = convert_time_24_to_12_format(in24)
            end, out_ampm = convert_time_24_to_12_format(out24)

            print("Enter time in: ", start, in_ampm)
            # Time In - with wait and refresh
            time_in_input = wait.until(EC.presence_of_element_located((
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[2]/input"
            )))
            time_in_input.clear()
            time_in_input.send_keys(start)
            
            time_in_ampm = wait.until(EC.presence_of_element_located((
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[3]/select"
            )))
            Select(time_in_ampm).select_by_visible_text(in_ampm)

            print("Enter time out: ", end, out_ampm)
            # Time Out - with wait and refresh
            time_out_input = wait.until(EC.presence_of_element_located((
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[4]/input"
            )))
            time_out_input.clear()
            time_out_input.send_keys(end)
            
            time_out_ampm = wait.until(EC.presence_of_element_located((
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[5]/select"
            )))
            Select(time_out_ampm).select_by_visible_text(out_ampm)

        # Save button - with wait and refresh
        print("Clicking on save button ...")
        save_button = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "/html/body/div[3]/form/table[3]/tbody/tr[2]/td/input[2]"
        )))
        save_button.click()


        print("CLicking on back button ...")
        # Back button - with wait and refresh
        back_button = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "/html/body/div[3]/form/table[3]/tbody/tr[1]/td/input[1]"
        )))
        back_button.click()

        # Wait for main table
        wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/div[3]/table[1]/tbody/tr[5]/td"
        )))

        return True

    except Exception as e:
        print("Error in enter_all_hours:", e)
        return False



def time_entries_each_day_to_time_sheet(driver):
    """
    Walks each date column, reads shifts from OpenClock DB,
    and calls enter_all_hours when needed.
    """
    date_list = []
    flag = False
    try:
        db_local = database_setup()
        while True:
            # Wait for the main table to be present and get fresh references
            wait = WebDriverWait(driver, 10)
            table = wait.until(EC.presence_of_element_located((By.XPATH,
                "/html/body/div[3]/table[1]/tbody/tr[5]/td"
            )))
            
            # Get fresh references to rows and cells
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) < 2:
                return [], False

            header_cells = rows[0].find_elements(By.TAG_NAME, "td")
            action_cells = rows[1].find_elements(By.TAG_NAME, "td")

            for idx, cell in enumerate(header_cells):
                shifts = []
                raw, is_date = convert_to_date(cell.text.strip())
                if not is_date:
                    continue

                date_list.append((raw, idx))

                print("Choose an option: A) OpenClock, B) Google Calendar")
                choice = input("Enter the letter of the option you want to select:  ").upper()
                if choice == "A":
                    # Query our DB
                    print("Query from Open Hours.... ")
                    entries = query_hours_entries_openclock(db_local, USERNAME, raw)
                    res = [shifts.append((e[3], e[4])) for e in entries if e[5] != 0]

                    print("Open Hours Shifts: ", res)
                elif choice == "B":
                    print("Query from Google Calender....")
                    print("Raw date: ", raw)
                    
                    entries = gcal_get_data(db_local, USERNAME, raw)
                    print("Get data: ",  entries)
                    if not entries:
                        entries = insert_gcal_data(db_local, USERNAME, raw)
                        print("Entries: ", entries)
                        if entries is None:
                            continue
                    
                    if entries:
                        if isinstance(entries, tuple):
                            shifts.append((entries[3], entries[4]))
                        else:
                            for e in entries:
                                shifts.append((e[3], e[4]))
                    print("G Cal Shifts: ", shifts)

                # Get fresh reference to action cell
                print("Action cell text:", action_cells[idx].text)
                if shifts and action_cells[idx].text == "Enter Hours":
                    print("Entering for input hours...")
                    action_cells[idx].find_element(
                        By.PARTIAL_LINK_TEXT, "Enter Hours"
                    ).click()
                    
                    # Wait for the form to be present
                    wait.until(EC.presence_of_element_located((By.XPATH,
                        "/html/body/div[3]/form/table[2]/tbody/tr[2]/td[2]/input"
                    )))
                    
                    is_success = enter_all_hours(driver, shifts)
                    if is_success:
                        print("Hours entered successfully")
                    else:
                        print("Error entering hours")

            # Get fresh reference to navigation table
            nav_table = wait.until(EC.presence_of_element_located((
                By.XPATH, 
                "/html/body/div[3]/table[1]/tbody/tr[5]/td/form/table[2]/tbody"
            )))
            nav_buttons = nav_table.find_elements(By.TAG_NAME, "input")
            
            if nav_buttons:
                next_button = nav_buttons[-1]
                if next_button.get_attribute("value") == "Next":
                    print("Found Next button, clicking...")
                    next_button.click()
                    # Wait for the page to update
                    wait.until(EC.staleness_of(nav_table))
                    continue
                elif flag == False and next_button.get_attribute("value") == "Previous":
                    flag = True
                    continue
                else:
                    print("No Next button found, we're on the last page")
                    break

        return date_list, True

    except Exception as e:
        print("Error in time_entries_each_day_to_time_sheet:", e)
        return [], False

    finally:
        db_local.close()


def parse_line(line):
    """Parses lines like 'May 11, 2025 to May 24, 2025 In Progress'."""
    m = re.match(
        r"([A-Za-z]{3,9} \d{1,2}, \d{4}) to "
        r"([A-Za-z]{3,9} \d{1,2}, \d{4}) (.+)",
        line
    )
    if not m:
        raise ValueError(f"Line format incorrect: {line}")
    s, e, stt = m.groups()
    return {
        "start_date": datetime.strptime(s, "%b %d, %Y"),
        "end_date":   datetime.strptime(e, "%b %d, %Y"),
        "status":     stt
    }


def setup_driver():
    """Starts ChromeDriver with a fresh profile directory."""
    path = "../chromedriver-mac-arm64/chromedriver"
    if not os.path.exists(path):
        raise FileNotFoundError(f"ChromeDriver not found: {path}")
    service = Service(path)
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--user-data-dir=./chrome_profile_{int(time.time())}")
    return webdriver.Chrome(service=service, options=opts)


def login_to_self_service(driver, username, password):
    """
    Navigates the self-service site, performs Duo if needed,
    then returns a list of period dicts.
    """
    # initial login
    if "selfservice.manhattan.edu" not in driver.current_url:
        driver.get("https://selfservice.manhattan.edu/")
        driver.find_element(By.ID, "read-link-0").click()
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.NAME, "_eventId_proceed").click()

        wait = WebDriverWait(driver, 20)
        duo = wait.until(EC.presence_of_element_located((By.ID, "header-text")))
        if duo.text == "Enter code in Duo Mobile":
            code = driver.find_element(By.CLASS_NAME, "verification-code").text
            print(f"Enter this code in Duo Mobile: {code}")
            # wait for trust prompt
            while True:
                try:
                    if driver.find_element(
                        By.ID, "trust-this-browser-label"
                    ).text == "Is this your device?":
                        driver.find_element(
                            By.ID, "trust-browser-button"
                        ).click()
                        time.sleep(5)
                        break
                except:
                    time.sleep(1)

    # navigate menus
    for xpath in [
        '//*[@id="bannerMenu"]',
        '//*[@id="list_Banner"]/div/div[1]/span',
        '//*[@id="list_Banner_Financial Aid"]/div/div[1]/span',
        '//*[@id="list_Banner_Financial Aid_Student Employment Menu"]/div/div[1]/span',
        '//*[@id="list_Banner_Financial Aid_Student Employment Menu_Enter Time Sheet"]/a/div/div/span'
    ]:
        driver.find_element(By.XPATH, xpath).click()
        time.sleep(2)

    # grab raw periods text
    sel = driver.find_element(By.ID, "period_1_id")
    raw = sel.text.split("\n")
    periods = [parse_line(line) for line in raw if line.strip()]
    print("Read from login: ", periods)

    if not periods:
        print("❌ No available time periods found")
        return None

    return periods

# This function is used to select a period from the terminal
def select_period_from_terminal(structured_data):
    """
    Presents the structured_data as lettered options in the terminal, prompts the user for a letter,
    and returns the selected period dictionary. Returns None if the selection is invalid.
    """
    print("Select a time period:")
    for idx, period in enumerate(structured_data):
        letter = string.ascii_uppercase[idx]
        print(f"{letter}) {period['start_date'].strftime('%b %d, %Y')} to {period['end_date'].strftime('%b %d, %Y')} - {period['status']}")

    choice = input("Enter the letter of the period you want to select: ").upper()
    try:
        selected_idx = string.ascii_uppercase.index(choice)
        selected_period = structured_data[selected_idx]
        print("You selected:", selected_period)
        return selected_period
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

def extract_time_from_self_service_and_select_period(driver):

    structured_data = login_to_self_service(driver, USERNAME, PASSWORD)
    # 1. Show options and get user selection
    selected_period = select_period_from_terminal(structured_data)
    if selected_period is not None:
        # 2. Find the index of the selected period
        selected_idx = structured_data.index(selected_period)
        # 3. Select the corresponding option in the dropdown
        select_elem = driver.find_element(By.ID, "period_1_id")
        select = Select(select_elem)
        select.select_by_index(selected_idx)
        print("Selected in browser:", selected_period)
        time.sleep(5)
        submit_time_selection = driver.find_element(By.XPATH, '/html/body/div[3]/form/table[2]/tbody/tr/td/input')
        print("Submit Time Selection:", submit_time_selection.text)
        submit_time_selection.click()
        time.sleep(3)
        _, desired_date_found = time_entries_each_day_to_time_sheet(driver)
        print("Desired date found:", desired_date_found)
        # if desired_date_found:
        #     print("Entering hours")
        #     result = enter_hours(driver, '10:00', '12:00', 'PM')
        #     print("Result:", result)
        #     return selected_period, result
        # else:
        #     print("Desired date not found")
        return selected_period
    else:
        print("No valid selection made.")



if __name__ == "__main__":
    driver = setup_driver()
    extract_time_from_self_service_and_select_period(driver)