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

def enter_hours(driver, start_time, end_time):
    try:
        start_time = driver.find_element(By.XPATH, '//*[@id="timein_input_id"]').send_keys(start_time)
        end_time = driver.find_element(By.XPATH, '//*[@id="timeout_input_id"]').send_keys(end_time)
        save_button = driver.find_element(By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[2]/td/input[2]").click()
        back_button = driver.find_element(By.XPATH, "/html/body/div[3]/form/table[3]/tbody/tr[1]/td/input[1]").click()
    except Exception as e:
        print("Error:", e)

def print_text_from_xpath(driver):
    date_list = []
    try:
        element = driver.find_element(By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td/form/table[1]/tbody")

        row_counter = 0
        for row in element.find_elements(By.TAG_NAME, "tr"):
            if row_counter >= 2:  # Stop after 2 rows
                break

            for col in row.find_elements(By.TAG_NAME, "td"):
                text = col.text.strip()
                date_list.append(text)
                print("Text found:", text)

            row_counter += 1

        print("Final date list:", date_list)
        return date_list

    except Exception as e:
        print("Error:", e)

def nextAndPrevious(driver):
    try:
        next_button = driver.find_element(By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[5]/td/form/table[2]/tbody/tr/td[6]/input")
        print(next_button.get_attribute("value"))
        next_button.click()
        time.sleep(5)
        print_text_from_xpath(driver)
    except Exception as e:
        print("Error:", e)
   
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

driver = setup_driver()

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
def extract_time_from_self_service(driver):

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
        return selected_period
    else:
        print("No valid selection made.")

timeframe = extract_time_from_self_service(driver)

submit_time_selection = driver.find_element(By.XPATH, '/html/body/div[3]/form/table[2]/tbody/tr/td/input')
print("Submit Time Selection:", submit_time_selection.text)
submit_time_selection.click()
time.sleep(5)

if __name__ == "__main__":
    # 1. Get all dates in the time period
    print_text_from_xpath(driver)
    nextAndPrevious(driver)








