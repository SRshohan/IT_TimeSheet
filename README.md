# IT Time Sheet Automation

This application helps automate the process of submitting your IT time sheet by extracting data from OpenClock or Google Calendar and automatically filling it into the Self-Service portal.

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- ChromeDriver (compatible with your Chrome version)
- Google Calendar API credentials (for Google Calendar integration)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SRshohan/IT_TimeSheet.git
cd IT_TimeSheet
```

2. Create and activate a virtual environment (recommended):
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
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

5. Set up Google Calendar API (for Google Calendar integration):
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

1. Start the application:
```bash
cd backend
streamlit run app.py
```

2. The application will open in your default web browser
3. Enter your credentials in the sidebar
4. Select the date range for time sheet extraction
5. Choose your data source (OpenClock or Google Calendar)
6. Click "Extract Data" to fetch your time entries
7. Click "Enter Time Sheet" to automatically fill the time sheet in Self-Service

## Features

- Automatic data extraction from OpenClock or Google Calendar
- Automatic time sheet entry in Self-Service portal
- Date range selection
- Secure credential management
- Real-time status updates
- Multiple data source options

## Troubleshooting

1. If you encounter ChromeDriver issues:
   - Ensure ChromeDriver version matches your Chrome browser version
   - Verify ChromeDriver is in the correct directory
   - Check if ChromeDriver has executable permissions

2. If the application fails to connect:
   - Verify your internet connection
   - Check if your credentials are correct
   - Ensure you have access to both OpenClock and Self-Service portals

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