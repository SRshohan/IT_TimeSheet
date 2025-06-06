# import extract_time
import sqlite3
from datetime import datetime, timedelta
from gCal import fetch_events_for_day, get_calendar_service
# import setup
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

calendar_id = os.getenv("CALENDAR_ID")


def convert_decimal_to_hms(decimal_hours):
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    seconds = int(((decimal_hours - hours) * 60 - minutes) * 60)
    return str(timedelta(hours=hours, minutes=minutes, seconds=seconds))


def database_setup():
    conn = sqlite3.connect("app.db")
    return conn

def create_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Daily hours entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hours_entries_openclock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            shift_in TIME NOT NULL DEFAULT '00:00',
            shift_out TIME NOT NULL DEFAULT '00:00',
            hours_worked REAL NOT NULL DEFAULT 0,
            notes TEXT DEFAULT 'No notes',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS time_entry_eachday_self_service_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'No',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
    

    conn.commit()
    conn.close()
    print("Database created with users and hours_entries tables.")


def insert_user(conn, first_name, username, password):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (first_name, username, password_hash)
        VALUES (?, ?, ?)
        ''', (first_name, username, password))
    conn.commit()

def insert_gcal_data(conn, user_name, date):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (user_name,))
    user = cursor.fetchone()
    if not user:
        print("User not found")
        return
    user_id = user[0]

    # Get event data from Google Calendar
    try:
        service = get_calendar_service()
        event = fetch_events_for_day(service, calendar_id, date)
        entry_date = event["date"]
        shift_in = event["start_time"]
        shift_out = event["end_time"]
        hours_worked = event["duration"]
    except Exception as e:
        print("Error fetching event data:", e)
        return

    # Check for existing entry with same user and date
    cursor.execute('''
        SELECT id, shift_out FROM hours_entries_openclock 
        WHERE user_id = ? AND entry_date = ?
    ''', (user_id, entry_date))
    existing_entry = cursor.fetchone()

    if existing_entry:
        existing_id, existing_shift_out = existing_entry

        # Check if shift_out is '00:00:00'
        if existing_shift_out == '00:00:00':
            # Perform update
            cursor.execute('''
                UPDATE hours_entries_openclock
                SET shift_in = ?, shift_out = ?, hours_worked = ?, notes = ?
                WHERE id = ?
            ''', (shift_in, shift_out, hours_worked, "GCal", existing_id))
            print(f"Updated entry on {entry_date}")
        else:
            print(f"Entry for {entry_date} already exists and has shift_out = {existing_shift_out}, no update needed.")
    else:
        # Perform insert
        cursor.execute('''
            INSERT INTO hours_entries_openclock (user_id, entry_date, shift_in, shift_out, hours_worked, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, entry_date, shift_in, shift_out, hours_worked, "GCal"))
        print(f"Inserted new entry for {entry_date}")

    conn.commit()
    print("Inserted:", entry_date, shift_in, shift_out, hours_worked)


def parse_row_and_insert_from_openclock(conn, user_name, row):
    if len(row) < 6:
        print("Row incomplete:", row)
        return

    try:
        # Convert '01/02, Thu' to 'YYYY-MM-DD'
        raw_date = row[0].split(',')[0].strip()  # '01/02'
        year = datetime.now().year
        
        entry_date = datetime.strptime(f"{year}/{raw_date}", "%Y/%m/%d").date()

        # Convert shift_in and shift_out to datetime objects
        shift_in_str = row[1].strip()
        shift_out_str = row[2].strip()
        
        # Handle missing or invalid times
        if shift_out_str == "missing" or shift_out_str == "00:00 AM":
            shift_out_str = "12:00 AM"
        if shift_in_str == "00:00 AM":
            shift_in_str = "12:00 AM"

        try:
            shift_in_dt = datetime.strptime(shift_in_str, "%I:%M %p")
            shift_out_dt = datetime.strptime(shift_out_str, "%I:%M %p")
        except ValueError as e:
            print(f"Invalid time format: {shift_in_str} or {shift_out_str}")
            return

        # Calculate total hours worked (as float)
        hours_worked = round((shift_out_dt - shift_in_dt).total_seconds() / 3600, 2)

        if hours_worked <= 0:
            date = datetime.strptime(f"{year}/{raw_date}", "%Y/%m/%d")
            date = date.strftime("%Y-%m-%d")
            date = datetime.strptime(date, "%Y-%m-%d")
            print("Inserting GCal data for", date, type(date))
            insert_gcal_data(conn, user_name, date)
            return
        

        # Get user ID from username
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (user_name,))
        user_result = cursor.fetchone()
        if not user_result:
            print(f"User {user_name} not found")
            return
        user_id = user_result[0]

        # Check for duplicate entries
        find_same_time_and_date = cursor.execute('SELECT * FROM hours_entries_openclock WHERE user_id = (?) AND entry_date = (?) AND shift_in = (?) AND shift_out = (?)', 
            (user_id, entry_date, shift_in_dt.strftime("%H:%M:%S"), shift_out_dt.strftime("%H:%M:%S")))
        if find_same_time_and_date.fetchone():
            print("Same time and date already exists")
            return

        # Insert the row
        cursor.execute('''
            INSERT INTO hours_entries_openclock (user_id, entry_date, shift_in, shift_out, hours_worked, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            entry_date,
            shift_in_dt.strftime("%H:%M:%S"),
            shift_out_dt.strftime("%H:%M:%S"),
            convert_decimal_to_hms(hours_worked),
            row[-1].strip() if row[-1] else 'No notes'
        ))

        conn.commit()
        print("Inserted:", entry_date, shift_in_str, shift_out_str, hours_worked)

    except Exception as e:
        print("Error inserting row:", e)

def insert_time_entries(conn, user_name, row):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (user_name,))
    user_id = cursor.fetchone()[0]

    cursor.execute('''
        INSERT INTO time_entry_eachday_self_service_status (user_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            row["start_date"],
            row["end_date"],
            row["status"]
        ))
    conn.commit()
    print("Inserted:", row["start_date"], row["end_date"])


def query_hours_entries_openclock(conn, user_name, entry_date):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (user_name,))
    user_id = cursor.fetchone()[0]
    res = cursor.execute('SELECT * FROM hours_entries_openclock WHERE user_id = (?) AND entry_date = (?)', (user_id, entry_date))
    if res:
        return cursor.fetchall()
    else:
        return None
    

if __name__ == "__main__":
    conn = database_setup()
    date_str = "2025-06-05"
    date = datetime.strptime(date_str, "%Y-%m-%d")
    print(type(date))
    insert_gcal_data(conn, "srahman06", date)


# if __name__ == "__main__":
#     username = "srahman06"

#     db = database_setup()
#     driver = setup.setup_driver()
#     create_db()
#     print("Driver setup complete")
#     selected_period = setup.extract_time_from_self_service_and_select_period(driver)
#     print("Selected period from self service:", selected_period)

#     def extractTimePeriodSelfService(data: dict):
#         insert_time_entries(db, username, data)
#         print("Inserted time entries from organizeData.py:", data)
#         return data

#     def check_user_exists(db, username):
#         cursor = db.cursor()
#         cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
#         return cursor.fetchone() is not None
    
#     if not check_user_exists(db, username):
#         insert_user(db, "Sohanur", username, "sohanur")

#     extractTimePeriodSelfService(selected_period)
    
#     data = extract_time.select_range_dates(username, "05/27/2025", "05/31/2025")
#     print(data)
#     parse_row_and_insert_from_openclock(db, username, data[0])
    # def convert_date_to_required_format(date):
    #     date_obj = datetime.strptime(date, "%Y-%m-%d")

    #     # Convert to required format
    #     formatted_date = date_obj.strftime("%A\n%b %d, %Y")

    #     return formatted_date
    # conn = database_setup()
    # data = query_hours_entries_openclock(conn, "srahman06", "2025-05-27")
    
    # print(convert_date_to_required_format(data[0][2]))












