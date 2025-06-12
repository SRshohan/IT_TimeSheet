# IT Time Sheet Automation

This application helps automate the process of submitting your IT time sheet by extracting data from Google Calendar and automatically filling it into the Self-Service portal.

> **FYI Note**: Currently, the application shows both OpenClock and Google Calendar options in the Self-Service submission process, but only Google Calendar integration is functional. You will need to select option "B" (Google Calendar) for each date entry. This can be streamlined by modifying the input selection at the top of the script.

## Prerequisites

- Python 3.11
- Chrome browser installed
- ChromeDriver (compatible with your Chrome version)
- Google Calendar API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SRshohan/IT_TimeSheet.git
cd IT_TimeSheet
```

2. Create and activate a virtual environment (recommended):
```bash
# On macOS/Linux
python3.11 -m venv venv
source venv/bin/activate

# On Windows
python3.11 -m venv venv
.\venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Download ChromeDriver:
   - Visit [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)
   - Download the version that matches your Chrome browser version
   - Extract the chromedriver executable to the `chromedriver-mac-arm64` directory in the project root

5. Set up Google Calendar API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `credentials.json` in the project root
   - Create a `.env` file and add your `CALENDAR_ID`
   - To find your Calendar ID:
     1. Go to [Google Calendar](https://calendar.google.com)
     2. Click on the three dots (⋮) next to your calendar name in the left sidebar
     3. Select "Settings and sharing"
     4. Scroll down to "Integrate calendar"
     5. Copy the "Calendar ID" (it usually looks like `example@gmail.com` or `example@group.calendar.google.com`)
     6. Add it to your `.env` file as `CALENDAR_ID=your_calendar_id`

## Usage

1. Run the application:
```bash
cd backend
python setup.py
```

2. The application will:
   - Open a Chrome browser window
   - Navigate to the Self-Service portal
   - Prompt you to select a time period
   - For each date, you'll need to select option "B" (Google Calendar) to enter hours
   - Automatically fill in your time entries from Google Calendar

> **Note**: Make sure your `.env` file contains the necessary credentials:
> - `USERNAME`: Your Self-Service portal username
> - `PASSWORD`: Your Self-Service portal password
> - `CALENDAR_ID`: Your Google Calendar ID

## Features

- Automatic data extraction from Google Calendar
- Automatic time sheet entry in Self-Service portal
- Date range selection
- Secure credential management
- Real-time status updates

> **Upcoming Features**:
> - OpenClock integration (currently in development)
> - Automatic selection of data source
> - Batch processing of multiple dates

## Troubleshooting

1. If you encounter ChromeDriver issues:
   - Ensure ChromeDriver version matches your Chrome browser version
   - Verify ChromeDriver is in the correct directory
   - Check if ChromeDriver has executable permissions

2. If the application fails to connect:
   - Verify your internet connection
   - Check if your credentials in `.env` are correct
   - Ensure you have access to the Self-Service portal

3. For Google Calendar integration issues:
   - Verify your `credentials.json` is properly set up
   - Check if your `CALENDAR_ID` is correct in the `.env` file
   - Ensure you have granted necessary permissions to the application

## Security Notes

- Never commit your `.env` file or share your credentials
- The application stores credentials only in your local session
- All data is processed locally on your machine
- Google Calendar credentials are stored securely and only used for API access

## Support

For issues or questions, please open an issue in the repository.