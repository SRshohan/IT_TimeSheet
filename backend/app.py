from organizeData import database_setup, insert_time_entries, parse_row_and_insert_from_openclock, query_hours_entries_openclock
from setup import setup_driver, extract_time_from_self_service_and_select_period, enter_hours, time_entries_each_day_to_time_sheet
from extract_time import select_range_dates
from datetime import datetime



# This function is used to get the start and end date from the database
def get_start_and_end_date(db, username, status: str):
    cursor = db.cursor()
    # First get the user_id from username
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_id = cursor.fetchone()
    
    if user_id is None:
        print(f"No user found with username: {username}")
        return None
        
    user_id = user_id[0]  # Get the actual id value
    
    # Now query with the user_id
    cursor.execute('''
        SELECT start_date, end_date, status 
        FROM time_entry_eachday_self_service_status 
        WHERE user_id = ? AND status = ?
    ''', (user_id, status))
    
    result = cursor.fetchone()
    if result is None:
        print(f"No time entry found for user {username} with status {status}")
        return None
        
    return {
        "start_date": result[0].split()[0],
        "end_date": result[1].split()[0],
        "status": result[2]
    }

# This function is used to convert the date to the required format
def convert_date_to_required_format(date):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%m/%d/%Y")
        return formatted_date

if __name__ == "__main__":
    username = "srahman06"
    db = database_setup()
    driver = setup_driver()
    selected_period = extract_time_from_self_service_and_select_period(driver)
    
    date_period = get_start_and_end_date(db, username, "In Progress")
    print("date_period", date_period)

    # This is the date period from the self service website
    start_date = convert_date_to_required_format(date_period["start_date"])
    print("start_date", start_date)
    end_date = convert_date_to_required_format(date_period["end_date"])
    print("end_date", end_date)
    dump = select_range_dates(username, start_date, end_date)
    for row in dump:
        print("row", row)
        parse_row_and_insert_from_openclock(db, username, row)


    
