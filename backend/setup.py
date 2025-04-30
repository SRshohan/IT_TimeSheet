from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time
from dotenv import load_dotenv

load_dotenv()

path = "../chromedriver-mac-arm64/chromedriver"

if not os.path.exists(path):
    raise Exception("Path doesn't exist!")

service = Service(path)
options = Options()
# options.add_argument("--headless=new")  # Uncomment if you want background mode

driver = webdriver.Chrome(service=service)

driver.get("https://selfservice.manhattan.edu/")

# Click the "Sign In Via JasperNet" link
driver.find_element(By.ID, "read-link-0").click()


# Now type the username
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver.find_element(By.ID, "username").send_keys(username)
driver.find_element(By.ID, "password").send_keys(password)
driver.find_element(By.NAME, "_eventId_proceed").click()
time.sleep(10)

duo_header = driver.find_element(By.ID, "header-text")

if duo_header.text == "Enter code in Duo Mobile":
    print(duo_header.text)
    element = driver.find_element(By.CLASS_NAME, "verification-code")
    code = element.text
    print(code)













