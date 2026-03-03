# Google Sheets API Setup Guide

Follow these steps to set up Google Sheets API integration for your GROWW OI Data script.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on "Select a project" at the top
3. Click "NEW PROJECT"
4. Enter a project name (e.g., "GROWW OI Tracker")
5. Click "CREATE"

## Step 2: Enable Google Sheets API

1. In the Google Cloud Console, go to **APIs & Services > Library**
2. Search for "Google Sheets API"
3. Click on it and press **ENABLE**
4. Also search for "Google Drive API" and **ENABLE** it

## Step 3: Create a Service Account

1. Go to **APIs & Services > Credentials**
2. Click **CREATE CREDENTIALS** > **Service Account**
3. Enter a service account name (e.g., "groww-oi-bot")
4. Click **CREATE AND CONTINUE**
5. Skip the optional steps (click **CONTINUE**, then **DONE**)

## Step 4: Create and Download Credentials

1. Click on the service account you just created
2. Go to the **KEYS** tab
3. Click **ADD KEY** > **Create new key**
4. Choose **JSON** format
5. Click **CREATE**
6. A JSON file will be downloaded to your computer

## Step 5: Setup the Credentials File

1. Rename the downloaded JSON file to `credentials.json`
2. Move it to your project folder (same location as TEST.PY):
   ```
   C:\Users\gouthamsankar\Downloads\GROW\credentials.json
   ```

## Step 6: Share the Google Sheet (First Time Only)

After running the script for the first time:

1. The script will create a Google Sheet named "GROWW OI Data"
2. Open your Google Drive at https://drive.google.com
3. Find the "GROWW OI Data" spreadsheet
4. Click **Share**
5. Add your email address with **Editor** permissions
6. Now you can access the sheet from your Google Drive!

**OR**

If you want to use an existing spreadsheet:
1. Open your existing Google Sheet
2. Click **Share**
3. Copy the **service account email** from your `credentials.json` file
   - It looks like: `groww-oi-bot@project-name.iam.gserviceaccount.com`
4. Paste it in the Share dialog and give it **Editor** permissions
5. Modify the script to use your sheet name:
   ```python
   sheet_name="Your Existing Sheet Name"
   ```

## Troubleshooting

### Error: "credentials.json not found"
- Make sure the file is in the same directory as TEST.PY
- Check the filename is exactly `credentials.json` (case-sensitive)

### Error: "Insufficient Permission"
- Make sure Google Sheets API and Google Drive API are both enabled
- The service account needs Editor access to the spreadsheet

### Error: "Spreadsheet not found"
- The spreadsheet will be created automatically on first run
- Check your Google Drive for "GROWW OI Data"
- The script will print the spreadsheet URL

## Script Configuration

By default, the script writes to a sheet named "GROWW OI Data". To customize:

In TEST.PY, find the `write_to_google_sheets()` call and modify:

```python
sheet_url = write_to_google_sheets(
    data_rows=all_data_rows,
    fieldnames=fieldnames,
    sheet_name="YOUR_CUSTOM_NAME",  # Change this
    credentials_file="credentials.json"
)
```

## Success!

Once setup is complete, the script will:
1. ✅ Save data to CSV file (GROWW_OI_Export.csv)
2. ✅ Write data to Google Sheets
3. ✅ Print the Google Sheets URL for easy access

You can then access your data from anywhere via Google Sheets!
