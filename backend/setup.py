from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()


def setup_driver():

    path = "../chromedriver-mac-arm64/chromedriver"

    if not os.path.exists(path):
        raise Exception("Path doesn't exist!")

    service = Service(path)
    options = Options()
    # options.add_argument("--headless=new")  # Uncomment if you want background mode

    driver = webdriver.Chrome(service=service)

    return driver

driver = setup_driver()

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
    time.sleep(20)
    trust_screen = driver.find_element(By.ID, "trust-this-browser-label")
    print(trust_screen.text)
    if trust_screen.text == "Is this your device?":
        driver.find_element(By.ID, "trust-browser-button").click()
        time.sleep(5)
        driver.get("https://banner-ssb-prod.manhattan.edu/PROD/bwpktais.P_SelectTimeSheetRoll")
        time.sleep(10)
        # click_banner_menu.click()
        # print("Clicked banner menu")
        # time.sleep(5)
        # driver.find_element(By.ID, "menuList").click()
        # print("Clicked Banner common Menu!")
        # driver.find_element(By.CLASS_NAME, "menu-common").click()
        # driver.find_element(By.ID, "menuList").click()
        # driver.find_element(By.CLASS_NAME, "menu-text menu-common").click()
    else:
        print("Duo is not working")
else:
    print(duo_header.text)


