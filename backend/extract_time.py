import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os

# Collect data from the website
data = []

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

# Extract headers
headers = table.find_elements(By.TAG_NAME, "th")
header_texts = [header.text for header in headers]

# Extract all rows
rows = table.find_elements(By.TAG_NAME, "tr")
for row in rows:
    cells = row.find_elements(By.TAG_NAME, "td")
    cell_texts = [cell.text for cell in cells]
    if len(cell_texts) > 0:
        cell_texts = extract_text(cell_texts[0])
        data.append(cell_texts)

print(data)

# header_texts = extract_text(header_texts[0])
# for header in header_texts:
#     print(header)





