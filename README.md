# GROWW OI Tracker 📊

A Python-based tool to fetch **Put Option Open Interest (OI)** data from the Groww API for NSE stocks and automatically export to Google Sheets on a schedule.

**Perfect for GitHub Actions cron jobs!** ⏰

## Features

✅ **Parallel Processing** - 5 concurrent workers for fast data fetching  
✅ **Smart Filtering** - Only collects PE options at 5%+ OTM with open interest  
✅ **30MAR Expiry** - Pre-filtered for March 30 expiry options  
✅ **Timestamped Sheets** - Each run creates a new sheet with date & time  
✅ **Real-time Updates** - Writes to Google Sheets every 5 symbols  
✅ **CSV Export** - Saves data locally as backup  
✅ **GitHub Actions Ready** - Schedule runs at 9:30 AM, 11:30 AM, 1:30 PM, 3:00 PM  

## Data Columns

| Column | Description |
|--------|-------------|
| Date | Last trade timestamp |
| Symbol | Stock symbol (e.g., RELIANCE) |
| Expiry | Option expiry (e.g., 30MAR) |
| Strike | Strike price |
| Type | Option type (always PE) |
| LTP | Last traded price |
| Volume | Trading volume |
| OI | Open interest |
| OI Change % | Percentage change in OI |
| Underlying Value | Current stock price |

## Setup

### 1. Prerequisites

- Python 3.8+
- A Groww API account with credentials
- A Google Sheets document
- A Google Service Account with Sheets API access

### 2. Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/groww-oi-tracker.git
cd groww-oi-tracker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get Groww Credentials

1. Log in to [Groww](https://groww.in)
2. Go to Settings → API Integration
3. Copy your **API Key** and **Secret**
4. Create `TEST.txt` with:
   ```
   Line 1: (blank)
   Line 2: YOUR_API_KEY
   Line 3-5: (blank)
   Line 6: YOUR_SECRET
   ```

### 4. Get Google Sheets Credentials

See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) for detailed steps:

1. Create a Google Cloud Project
2. Enable Sheets API & Drive API
3. Create a Service Account
4. Download JSON credentials → `credentials.json`
5. Share your Google Sheet with the service account email

**Update the spreadsheet ID in TEST.PY (line ~440):**
```python
SPREADSHEET_ID = "your-spreadsheet-id-here"
```

### 5. Run Locally

```bash
python TEST.PY
```

Each run creates a new timestamped sheet: `2026-03-03_0930`

## GitHub Actions Setup

### 1. Verify Workflow File

The workflow file is pre-configured at `.github/workflows/groww-oi-tracker.yml` with:
- **4 scheduled runs:** 9:30 AM, 11:30 AM, 1:30 PM, 3:00 PM UTC (Mon-Fri)
- **Automatic credential setup** from GitHub Secrets
- **Artifact upload** of CSV results

**Time Zone Note:**
- Cron times are in UTC (Coordinate Universal Time)
- For IST (UTC+5:30): Add 5.5 hours to the times above
  - 9:30 AM UTC = 3:00 PM IST
  - 11:30 AM UTC = 5:00 PM IST
  - 1:30 PM UTC = 7:00 PM IST
  - 3:00 PM UTC = 8:30 PM IST

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and create these three secrets:

#### `GROWW_API_KEY`
Your Groww API Key (from Settings → API Integration)

#### `GROWW_SECRET`
Your Groww API Secret (from Settings → API Integration)

#### `GOOGLE_CREDENTIALS_JSON`
The entire contents of your `credentials.json` file (as a JSON string)

To add this secret:
1. Copy the full contents of your `credentials.json`
2. Go to GitHub Secrets
3. Create `GOOGLE_CREDENTIALS_JSON`
4. Paste the JSON contents

⚠️ **CRITICAL:** Never commit these secrets to the repository!

### 3. Automatic Credential Handling

The script automatically detects the environment:

**Running locally:**
- Reads from `TEST.txt` and `credentials.json` files

**Running in GitHub Actions:**
- Reads from GitHub Secrets via environment variables
- Automatically creates `TEST.txt` and `credentials.json` from secrets
- Runs TEST.PY with credentials

No manual intervention needed!

## File Structure

```
groww-oi-tracker/
├── TEST.PY                         # Main script ✅
├── requirements.txt                # Python dependencies ✅
├── .gitignore                     # Exclude sensitive files ✅
├── GOOGLE_SHEETS_SETUP.md         # Google Sheets setup guide ✅
├── README.md                      # This file ✅
├── .github/
│   └── workflows/
│       └── groww-oi-tracker.yml   # GitHub Actions cron job ✅
│
├── TEST.txt                       # ❌ NOT in repo (in .gitignore)
├── credentials.json               # ❌ NOT in repo (in .gitignore)
└── GROWW_OI_Export.csv           # ❌ Output file (in .gitignore)
```

## Watchlist Symbols

The script monitors **100+ NSE stocks** including:

360ONE, ABB, ABBOTINDIA, RELIANCE, TCS, INFY, HDFC, ICICIBANK, AXISBANK, BAJAJFINSV, and many more...

See the `watchlist` variable in TEST.PY for the complete list.

## Key Configuration

**In TEST.PY (around line 440):**

```python
SPREADSHEET_ID = "your-spreadsheet-id-here"  # ⚠️ UPDATE THIS!
CREDENTIALS_FILE = "credentials.json"        # Google credentials
```

**To get your SPREADSHEET_ID:**
1. Open your Google Sheet in browser
2. The URL will be: `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit`
3. Copy the part after `/d/` and before `/edit`
4. Replace `"your-spreadsheet-id-here"` with your actual ID

**Parallel Workers:** Currently set to 5 (can be changed in line ~464)

## Troubleshooting

### "Permission denied" on Google Sheets
→ Make sure you shared the sheet with the service account email

### "Module not found" errors
→ `pip install -r requirements.txt`

### API rate limiting
→ The script has built-in delays; if issues persist, increase `time.sleep()` values

### Sheet name format
→ Sheets are created as `YYYY-MM-DD_HHMM` (e.g., `2026-03-03_0930`)

## License

MIT License - Feel free to use and modify!

## Support

For issues or questions:
- Check [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
- Review test output in GitHub Actions logs
- Verify credentials are correct

---

**Last Updated:** March 3, 2026
