from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()

calendar_id = os.getenv("CALENDAR_ID")

# Define the scope for read-only access to calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Step 1: Authenticate and build the service
def get_calendar_service():
    creds = None
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    except Exception:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


# 
def fetch_events_for_day(service, calendar_id, specific_date):
    # Set start and end of the specific day (in UTC)
    time_min = specific_date.isoformat() + 'Z'
    time_max = (specific_date + timedelta(days=1)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    result = {}

    for event in events:
        summary = event.get('summary', 'No Title')

        if summary == "Sohanur Rahman":
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            end_str = event['end'].get('dateTime', event['end'].get('date'))

            try:
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
                start_date = start_dt.date()
                start_time = start_dt.time().strftime("%H:%M:%S")
                end_time = end_dt.time().strftime("%H:%M:%S")
                duration = end_dt - start_dt
            except:
                # Handle all-day event or bad formatting
                start_date = start_str
                start_time = "All Day"
                end_time = "All Day"
                duration = "All Day"

            print(f"\nEvent: {summary}")
            print(f"Date:  {start_date}")
            print(f"Start: {start_time}")
            print(f"End:   {end_time}")
            print(f"Duration: {duration}")

            result = {
                'date': str(start_date),
                'start_time': start_time,
                'end_time': end_time,
                'duration': str(duration)
            }
            break  # Stop after first matching event
        else:
            print(f"Event: {summary}, skipping...")

    return result



# Step 3: Run it
def main():

    # Set the date you want to search (YYYY, MM, DD)
    specific_date = datetime(2025, 6, 5)

    service = get_calendar_service()
    events = fetch_events_for_day(service, calendar_id, specific_date)

    if not events:
        print("No events found.")
        return

    for event in events:
        summary = event.get('summary', 'No Title')
        if summary == "Sohanur Rahman":
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Try to calculate duration
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                duration = end_dt - start_dt
            except:
                duration = 'All day'

            print(f"\nEvent: {summary}")
            print(f"Start: {start}")
            print(f"End:   {end}")
            print(f"Duration: {duration}")
        else:
            print(f"Event: {summary}, Skipping...")

if __name__ == '__main__':
    main()

