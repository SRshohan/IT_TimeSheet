import time
from setup import setup_driver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Collect data from the website
data = []

# Setup driver
driver = setup_driver()
# WebDriverWait
wait = WebDriverWait(driver, 10)

driver.get("https://www.opentimeclock.com/free.html?page=2004&v=1665245702874")

wait.until(EC.element_to_be_clickable((By.ID, "txtUser"))).send_keys("srahman06")

wait.until(EC.element_to_be_clickable((By.ID, "txtPassword"))).send_keys("sohanur")

wait.until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

# Wait for the table or a known element to be present
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[style='text-align:center;width:90px;float:left;']")))

# Extract all date cells
date_divs = driver.find_elements(By.CSS_SELECTOR, "div[style='text-align:center;width:90px;float:left;']")
for div in date_divs:
    print(div.text)

# If you want to extract entire rows, you may need to adjust the selector

driver.quit()




