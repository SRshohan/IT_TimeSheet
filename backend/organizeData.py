import extract_time
import sqlite3
from datetime import datetime
import setup

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
            date DATE NOT NULL,
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


def parse_row_and_insert(conn, user_name, row):
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
        if shift_out_str == "missing":
            shift_out_str = "00:00 AM"
        else:
            shift_out_str = row[2].strip()

        shift_in_dt = datetime.strptime(shift_in_str, "%I:%M %p")
        print(shift_in_dt)
        shift_out_dt = datetime.strptime(shift_out_str, "%I:%M %p")
        print(shift_out_dt)

        # Calculate total hours worked (as float)
        hours_worked = round((shift_out_dt - shift_in_dt).total_seconds() / 3600, 2)

        # Get user ID from username
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (user_name,))
        user_id = cursor.fetchone()[0]

        # Insert the row
        cursor.execute('''
            INSERT INTO hours_entries (user_id, entry_date, shift_in, shift_out, hours_worked, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            entry_date,
            shift_in_dt.strftime("%H:%M:%S"),
            shift_out_dt.strftime("%H:%M:%S"),
            hours_worked,
            row[-1].strip()
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
        INSERT INTO time_entries (user_id, entry_date, end_date, status)
        VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            row["start_date"],
            row["end_date"],
            row["status"]
        ))
    conn.commit()
    print("Inserted:", row["start_date"], row["end_date"])
    

if __name__ == "__main__":
    username = "srahman06"

    db = database_setup()
    driver = setup.setup_driver()
    print("Driver setup complete")
    selected_period = setup.extract_time_from_self_service(driver)
    print("Selected period from self service:", selected_period)

    def extractTimeSelfService(data: dict):
        insert_time_entries(db, username, data)
        print("Inserted time entries from organizeData.py:", data)
        return data

    def check_user_exists(db, username):
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        return cursor.fetchone() is not None
    
    if not check_user_exists(db, username):
        insert_user(db, "Sohanur", username, "sohanur")

    extractTimeSelfService(selected_period)
    
    # data = extract_time.select_range_dates(username, "05/27/2025", "05/31/2025")
    # print(data)
    # parse_row_and_insert(db, username, data[0])










