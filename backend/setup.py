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
from datetime import datetime
import re
import string


load_dotenv()

# This function is used to convert the date to a datetime object
def convert_to_date(date):
    try:
        date = date.split("\n")
        date = date[-1].strip()
        date = datetime.strptime(date, "%b %d, %Y")
        return (date, True)
    except ValueError:
        return (date, False)


# This function is used to enter the hours into the Each Day time sheet
def enter_hours(driver, start_time, end_time, am_pm):
    try:
        start_time = driver.find_element(By.XPATH, '//*[@id="timein_input_id"]').send_keys(start_time)
        end_time = driver.find_element(By.XPATH, '//*[@id="timeout_input_id"]').send_keys(end_time)
        am_pm_dropdown = driver.find_element(By.XPATH, '/html/body/div[3]/form/table[2]/tbody/tr[2]/td[5]/select')
        dropdown = Select(am_pm_dropdown)
        dropdown.select_by_visible_text(am_pm)
        save_button = driver.find_element(By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[2]/td/input[2]").click()
        back_button = driver.find_element(By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[1]/td/input[1]").click()
        return True
    except Exception as e:
        print("Error entering hours function:", e)
        return False


def time_entries_each_day_to_time_sheet(driver, desired_date):
    date_list = []
    try:
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

            if is_date and text == desired_date:
                print("Date found:", date)
                date_list.append((date, index))

                # ✅ Only interact with this element once (don't touch old DOM after click)
                enter_hours_link = action_cells[index].find_element(By.PARTIAL_LINK_TEXT, "Enter Hours")
                enter_hours_link.click()

                return date_list, True

        return date_list, False

    except Exception as e:
        print("Error:", e)
        return [], False



# This function is used to go to the next and previous page of the time sheet
def nextAndPrevious(driver):
    try:
        next_button = driver.find_element(By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td/form/table[2]/tbody/tr/td[6]/input")
        value = next_button.get_attribute("value")
        print(value)
        next_button.click()
        return value
    except Exception as e:
        print("Error:", e)
   

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

    choice = input("Enter your choice (A, B, C, ...): ").strip().upper()
    try:
        selected_idx = string.ascii_uppercase.index(choice)
        selected_period = structured_data[selected_idx]
        print("You selected:", selected_period)
        return selected_period
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

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
        raise Exception("Path doesn't exist!")

    service = Service(path)
    options = Options()
    # options.add_argument("--headless=new")  # Uncomment if you want background mode

    driver = webdriver.Chrome(service=service)

    return driver


# This function is used to login to the self service website
def login_to_self_service(driver):
    driver.get("https://selfservice.manhattan.edu/")

    # Click the "Sign In Via JasperNet" link
    driver.find_element(By.ID, "read-link-0").click()
    # Now type the username
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.NAME, "_eventId_proceed").click()

    wait = WebDriverWait(driver, 20)
    duo_header = wait.until(EC.presence_of_element_located((By.ID, "header-text")))

    if duo_header.text == "Enter code in Duo Mobile":
        print(duo_header.text)
        element = driver.find_element(By.CLASS_NAME, "verification-code")
        code = element.text
        print(code)
        time.sleep(10)
        trust_screen = driver.find_element(By.ID, "trust-this-browser-label")
        print(trust_screen.text)
        if trust_screen.text == "Is this your device?":
            driver.find_element(By.ID, "trust-browser-button").click()
            time.sleep(5)
            menu_button = driver.find_element(By.ID, "bannerMenu")
            menu_button.click()
            time.sleep(5)
            banner_text = driver.find_element(By.XPATH, '//*[@id="list_Banner"]/div/div[1]/span')
            print(banner_text.text)  # Output: Banner 
            banner_text.click()
            time.sleep(5)
            financial_aid = driver.find_element(By.XPATH, '//*[@id="list_Banner_Financial Aid"]/div/div[1]/span')
            print(financial_aid.text)
            financial_aid.click()
            time.sleep(5)
            student_employment = driver.find_element(By.XPATH, '//*[@id="list_Banner_Financial Aid_Student Employment Menu"]/div/div[1]/span')
            print(student_employment.text)
            student_employment.click()
            time.sleep(5) 
            time_sheet = driver.find_element(By.XPATH, '//*[@id="list_Banner_Financial Aid_Student Employment Menu_Enter Time Sheet"]/a/div/div/span')
            print(time_sheet.text)
            time_sheet.click()
            time.sleep(5)
            select_time_period = driver.find_element(By.XPATH, '//*[@id="period_1_id"]')
            print(select_time_period.text)
            raw_data = select_time_period.text.split('\n')  # <-- Fix is here
            select_time_period.click()
            structured_data = [parse_line(line) for line in raw_data if line.strip()]
            for period in structured_data:
                print(period)
            time.sleep(5)
            return structured_data
        else:
            print("Duo is not working")
    else:
        print(duo_header.text)



# This function is used to extract the time from the self service website
def extract_time_from_self_service_and_select_period(driver):

    structured_data = login_to_self_service(driver)
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
        _, desired_date_found = time_entries_each_day_to_time_sheet(driver, 'Monday\nMay 26, 2025')
        print("Desired date found:", desired_date_found)
        if desired_date_found:
            print("Entering hours")
            result = enter_hours(driver, '10:00', '12:00', 'PM')
            print("Result:", result)
            return selected_period, result
        else:
            print("Desired date not found")
            return selected_period, False
    else:
        print("No valid selection made.")


def enter_time_each_day(driver):
    time_entries = time_entries_each_day_to_time_sheet(driver)
    for time_entry in time_entries:
        enter_hours(driver, time_entry["start_date"], time_entry["end_date"])
        time.sleep(5)
        nextAndPrevious(driver)
        

# timeframe = extract_time_from_self_service(driver)

# submit_time_selection = driver.find_element(By.XPATH, '/html/body/div[3]/form/table[2]/tbody/tr/td/input')
# print("Submit Time Selection:", submit_time_selection.text)
# submit_time_selection.click()
# time.sleep(5)


if __name__ == "__main__":
    driver = setup_driver()
    # 1. Get all dates in the time period
    selected_period, result = extract_time_from_self_service_and_select_period(driver)
    print(selected_period, result)
    








