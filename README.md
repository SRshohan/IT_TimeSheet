# IT Time Sheet Automation

This application helps automate the process of submitting your IT time sheet by extracting data from OpenClock and automatically filling it into the Self-Service portal.

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- ChromeDriver (compatible with your Chrome version)

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



## Usage

1. Start the application:
```bash
cd backend
streamlit run app.py
```

2. The application will open in your default web browser
3. Enter your credentials in the sidebar
4. Select the date range for time sheet extraction
5. Click "Extract Data from OpenClock" to fetch your time entries
6. Click "Enter Time Sheet" to automatically fill the time sheet in Self-Service

## Features

- Automatic data extraction from OpenClock
- Automatic time sheet entry in Self-Service portal
- Date range selection
- Secure credential management
- Real-time status updates

## Troubleshooting

1. If you encounter ChromeDriver issues:
   - Ensure ChromeDriver version matches your Chrome browser version
   - Verify ChromeDriver is in the correct directory
   - Check if ChromeDriver has executable permissions

2. If the application fails to connect:
   - Verify your internet connection
   - Check if your credentials are correct
   - Ensure you have access to both OpenClock and Self-Service portals

## Security Notes

- Never commit your `.env` file or share your credentials
- The application stores credentials only in your local session
- All data is processed locally on your machine

## Support

For issues or questions, please open an issue in the repository.



