#!/usr/bin/env python3
# app.py
import argparse
from datetime import datetime, timedelta
from organizeData import (
    database_setup,
    parse_row_and_insert_from_openclock,
    query_hours_entries_openclock,
    insert_user,
    create_db
)
from setup import (
    setup_driver,
    login_to_self_service,
    extract_time_from_self_service_and_select_period
)
from extract_time import select_range_dates, is_data_up_to_date

def extract_openclock_data(username, password, start_date, end_date):
    """Extract data from OpenClock for the given date range."""
    try:
        db = database_setup()
        create_db()

        # ensure user exists
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cur.fetchone():
            insert_user(db, username, username, password)

        res = select_range_dates(username, password, start_date, end_date)
        if res["data"]:
            for row in res["data"]:
                parse_row_and_insert_from_openclock(db, username, row)
            print(f"✅ Stored data from {res['start_date']} to {res['end_date']}")
        else:
            print("⚠️ No OpenClock data for that range.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def enter_timesheet(username, password):
    """Enter time sheet data into Self-Service."""
    try:
        driver = setup_driver()
        result = extract_time_from_self_service_and_select_period(
            driver, username, password
        )
        if result:
            print("✅ Time entries processed!")
        else:
            print("❌ Failed to process time entries.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Time Sheet Automation Tool")
    parser.add_argument("--username", required=True, help="Your username")
    parser.add_argument("--openclock-password", required=True, help="OpenClock password")
    parser.add_argument("--selfservice-password", required=True, help="Self-Service password")
    parser.add_argument("--start-date", help="Start date (MM/DD/YYYY)", 
                       default=(datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y"))
    parser.add_argument("--end-date", help="End date (MM/DD/YYYY)",
                       default=datetime.now().strftime("%m/%d/%Y"))
    parser.add_argument("--action", choices=["extract", "enter", "both"], required=True,
                       help="Action to perform: extract data, enter timesheet, or both")

    args = parser.parse_args()

    if args.action in ["extract", "both"]:
        print("📊 Extracting OpenClock data...")
        extract_openclock_data(args.username, args.openclock_password, 
                             args.start_date, args.end_date)

    if args.action in ["enter", "both"]:
        print("📝 Entering time sheet data...")
        enter_timesheet(args.username, args.selfservice_password)

    # Check data status
    if is_data_up_to_date():
        print("✅ Your data is up to date")
    else:
        print("⚠️ Your data needs to be updated")

if __name__ == "__main__":
    main()




    