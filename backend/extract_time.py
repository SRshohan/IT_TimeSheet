from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
from selenium.webdriver.common.keys import Keys


def extract_text(text):
    return text.split("\n")


# Setup driver
# driver = setup_driver()
path = "../chromedriver-mac-arm64/chromedriver"

if not os.path.exists(path):
    raise Exception("Path doesn't exist!")

service = Service(path)
options = Options()
# options.add_argument("--headless=new")  # Uncomment if you want background mode

driver = webdriver.Chrome(service=service)
# WebDriverWait
wait = WebDriverWait(driver, 10)

driver.get("https://www.opentimeclock.com/free.html?page=2004&v=1665245702874")

wait.until(EC.element_to_be_clickable((By.ID, "txtUser"))).send_keys("srahman06")

wait.until(EC.element_to_be_clickable((By.ID, "txtPassword"))).send_keys("sohanur")

wait.until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

# Wait for the table to be present
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed")))

# Find the table
table = driver.find_element(By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed")


def select_range_dates(start_date, end_date):
    # Set the date range
    driver.find_element(By.ID, "txtStart").clear()
    driver.find_element(By.ID, "txtStart").send_keys(start_date)
    end_input = driver.find_element(By.ID, "txtEnd")
    end_input.clear()
    end_input.send_keys(end_date)
    end_input.send_keys(Keys.ENTER)
    print("Selected range dates and triggered search!")

    # Wait for the table to be replaced (stale) and reappear
    old_table = driver.find_element(By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed")
    WebDriverWait(driver, 10).until(EC.staleness_of(old_table))
    new_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed"))
    )

    # Now extract the table
    data = []
    data_dict = {}
    rows = new_table.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        cell_texts = [cell.text for cell in cells]
        if len(cell_texts) > 0:
            cell_texts = extract_text(cell_texts[0])
            data.append(cell_texts)
    for row in data:
        data_dict[row[0]] = row

    return data_dict

# Usage:
data_dict = select_range_dates("01/01/2025", "05/31/2025")
print(data_dict)







