from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sqlite3

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

def get_last_extraction_date():
    """Get the last date data was extracted from OpenClock"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='time_entry_eachday_self_service_status'
        ''')
        
        if not cursor.fetchone():
            print("Table time_entry_eachday_self_service_status does not exist yet")
            return None
            
        cursor.execute('''
            SELECT MAX(end_date) 
            FROM time_entry_eachday_self_service_status
        ''')
        last_date = cursor.fetchone()[0]
        conn.close()
        return last_date
    except Exception as e:
        print(f"Error getting last extraction date: {e}")
        return None

def is_data_up_to_date():
    """Check if the data is up to date (within 1 day of current date)"""
    last_date = get_last_extraction_date()
    if not last_date:
        return False
    
    try:
        # Split the date and time, take only the date part
        last_date = last_date.split()[0]  # This will remove the time part
        last_date = datetime.strptime(last_date, "%Y-%m-%d")
        current_date = datetime.now()
        return (current_date - last_date).days <= 1
    except Exception as e:
        print(f"Error checking if data is up to date: {e}")
        return False

def extract_text(text):
    return text.split("\n")

def select_range_dates(username, password, start_date=None, end_date=None):
    # If no dates provided, use last extraction date + 1 as start date
    if not start_date:
        last_date = get_last_extraction_date()
        if last_date:
            # Split the date and time, take only the date part
            last_date = last_date.split()[0]
            start_date = (datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%m/%d/%Y")
        else:
            # If no previous data, start from 30 days ago
            start_date = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    
    if not end_date:
        end_date = datetime.now().strftime("%m/%d/%Y")

    path = "../chromedriver-mac-arm64/chromedriver"
    if not os.path.exists(path):
        raise Exception("ChromeDriver not found!")

    service = Service(path)
    options = Options()
    options.add_argument("--headless=new")  # Run in headless mode for automation
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 5)  # Reduced wait time from 10 to 5 seconds

    try:
        driver.get("https://www.opentimeclock.com/free.html?page=2004&v=1665245702874")

        # Login
        wait.until(EC.element_to_be_clickable((By.ID, "txtUser"))).send_keys(username)
        wait.until(EC.element_to_be_clickable((By.ID, "txtPassword"))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

        # Wait for table and set date range
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed")))
        
        start_input = driver.find_element(By.ID, "txtStart")
        start_input.clear()
        start_input.send_keys(start_date)
        
        end_input = driver.find_element(By.ID, "txtEnd")
        end_input.clear()
        end_input.send_keys(end_date)
        end_input.send_keys(Keys.ENTER)

        # Wait for table refresh
        old_table = driver.find_element(By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed")
        wait.until(EC.staleness_of(old_table))
        new_table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table.table-striped.table-bordered.table-hover.table-condensed")))

        # Extract data
        data = []
        rows = new_table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                cell_texts = extract_text(cells[0].text)
                data.append(cell_texts)

        return {
            'data': data,
            'start_date': start_date,
            'end_date': end_date,
            'is_up_to_date': is_data_up_to_date()
        }

    finally:
        driver.quit()

# Usage:
# data_dict = select_range_dates("05/27/2025", "05/31/2025")
# print(data_dict)







