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

from organizeData import query_hours_entries_openclock, database_setup

load_dotenv()

# Database connection & creds
db = database_setup()
USERNAME = os.getenv("USERNAME")


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
    “Enter Hours” form for each row.
    """
    try:
        for i, (in24, out24) in enumerate(shifts):
            row = i + 2
            start, in_ampm = convert_time_24_to_12_format(in24)
            end, out_ampm = convert_time_24_to_12_format(out24)

            # Time In
            driver.find_element(
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[2]/input"
            ).send_keys(start)
            Select(driver.find_element(
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[3]/select"
            )).select_by_visible_text(in_ampm)

            # Time Out
            driver.find_element(
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[4]/input"
            ).send_keys(end)
            Select(driver.find_element(
                By.XPATH,
                f"/html/body/div[3]/form/table[2]/tbody/tr[{row}]/td[5]/select"
            )).select_by_visible_text(out_ampm)

        wait = WebDriverWait(driver, 10)
        # Save
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/div[3]/form/table[3]/tbody/tr[2]/td/input[2]"
        ))).click()
        # Back
        wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/div[3]/form/table[3]/tbody/tr[1]/td/input[1]"
        ))).click()
        # Wait for main table
        wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/div[3]/table[1]/tbody/tr[5]/td"
        )))
        return True

    except Exception as e:
        print("Error in enter_all_hours:", e)
        return False


def nextAndPrevious(driver):
    """Clicks Next if available, returns the button label."""
    try:
        btn = driver.find_element(By.XPATH,
            "/html/body/div[3]/table[1]/tbody/tr[5]/td/form/"
            "table[2]/tbody/tr/td[6]/input"
        )
        val = btn.get_attribute("value")
        if val == "Next":
            btn.click()
        return val
    except Exception as e:
        print("Error at Next and Previous:", e)
        return None


def time_entries_each_day_to_time_sheet(driver):
    """
    Walks each date column, reads shifts from OpenClock DB,
    and calls enter_all_hours when needed.
    """
    date_list = []
    try:
        db_local = database_setup()
        while True:
            wait = WebDriverWait(driver, 10)
            table = wait.until(EC.presence_of_element_located((By.XPATH,
                "/html/body/div[3]/table[1]/tbody/tr[5]/td"
            )))
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) < 2:
                return [], False

            header_cells = rows[0].find_elements(By.TAG_NAME, "td")
            action_cells = rows[1].find_elements(By.TAG_NAME, "td")

            for idx, cell in enumerate(header_cells):
                raw, is_date = convert_to_date(cell.text.strip())
                if not is_date:
                    continue

                date_list.append((raw, idx))
                # Query our DB
                entries = query_hours_entries_openclock(db_local, USERNAME, raw)
                shifts = [(e[3], e[4]) for e in entries if e[5] != 0]

                if shifts and action_cells[idx].text == "Enter Hours":
                    action_cells[idx].find_element(
                        By.PARTIAL_LINK_TEXT, "Enter Hours"
                    ).click()
                    wait.until(EC.presence_of_element_located((By.XPATH,
                        "/html/body/div[3]/form/table[2]/tbody/tr[2]/td[2]/input"
                    )))
                    enter_all_hours(driver, shifts)

            label = nextAndPrevious(driver)
            if label == "Previous":
                break
            else:
                wait.until(EC.presence_of_element_located((By.XPATH,
                    "/html/body/div[3]/table[1]/tbody/tr[5]/td"
                )))

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
            st.info(f"Enter this code in Duo Mobile: {code}")
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

    if not periods:
        st.error("No available time periods found")
        return None

    return periods


def select_period_radio(periods, key="time_period_select"):
    """
    Renders A), B), C)… as a Streamlit radio list and returns
    the chosen period dict.
    """
    letters = string.ascii_uppercase
    options = ["Pick One"]+[
        f"{letters[i]}) {p['start_date'].strftime('%b %d, %Y')} to "
        f"{p['end_date'].strftime('%b %d, %Y')} - {p['status']}"
        for i, p in enumerate(periods)
    ]
    choice = st.radio("Select a time period", options, key=key)
    idx = options.index(choice)
    return periods[idx]


def extract_time_from_self_service_and_select_period(driver, username, password):
    """
    Full end-to-end: login → radio picker → select in browser →
    process each-day entries.
    """
    periods = login_to_self_service(driver, username, password)
    
    if periods not in "Pick One":

        selected = select_period_radio(periods)
        # pick in the dropdown
        sel = driver.find_element(By.ID, "period_1_id")
        Select(sel).select_by_index(periods.index(selected))
        driver.find_element(
            By.XPATH,
            "/html/body/div[3]/form/table[2]/tbody/tr/td/input"
        ).click()
        time.sleep(2)

        date_list, success = time_entries_each_day_to_time_sheet(driver)
        return date_list if success else None
    
    
    








