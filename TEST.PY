import os
import sys
import time
import traceback
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from growwapi import GrowwAPI
import gspread
from google.oauth2.service_account import Credentials
from datetime import timezone, timedelta

def get_sheet_name_with_timestamp():
    """
    Generate a sheet name with current date and time in IST.
    Format: YYYY-MM-DD_HHMM (e.g., 2026-03-03_0930)
    """
    # Convert UTC to IST (UTC + 5:30)
    ist = timezone(timedelta(hours=5, minutes=30))
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(ist)
    sheet_name = now_ist.strftime('%Y-%m-%d_%H%M')
    
    print(f"⏰ Current time: UTC {now_utc.strftime('%H:%M:%S')} → IST {now_ist.strftime('%H:%M:%S')}")
    print(f"📊 Sheet name: '{sheet_name}' (Date_Time in IST)")
    
    return sheet_name

def get_credentials(env_file='.env'):
    """
    Reads API Key and Secret (both pairs) from .env file or environment variables.
    Returns list of dicts with 'api_key' and 'secret' (supports dual API keys)
    """
    creds_list = []
    
    # Load .env file if it exists
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded credentials from {env_file}")
    else:
        print(f"⚠️ .env file not found, using environment variables...")
    
    # Try to read first API key pair
    api_key_1 = os.getenv('GROWW_API_KEY')
    secret_1 = os.getenv('GROWW_SECRET')
    
    if api_key_1 and secret_1:
        creds_list.append({
            'api_key': api_key_1.strip(),
            'secret': secret_1.strip()
        })
        print(f"✅ Loaded API credential pair #1")
    
    # Try to read second API key pair
    api_key_2 = os.getenv('GROWW_API_KEY_2')
    secret_2 = os.getenv('GROWW_SECRET_2')
    
    if api_key_2 and secret_2:
        creds_list.append({
            'api_key': api_key_2.strip(),
            'secret': secret_2.strip()
        })
        print(f"✅ Loaded API credential pair #2")
    
    if len(creds_list) > 1:
        print(f"✅ Total: {len(creds_list)} API credential pairs loaded")
    elif len(creds_list) == 0:
        print(f"❌ Error: No API credentials found in .env or environment variables.")
        print(f"   Please create .env file with GROWW_API_KEY and GROWW_SECRET.")
    
    return creds_list

def write_to_google_sheets(data_rows, fieldnames, spreadsheet_id=None, credentials_file="credentials.json"):
    """
    Write data to Google Sheets.
    
    Args:
        data_rows: List of dictionaries containing row data
        fieldnames: List of column headers
        spreadsheet_id: Google Sheets spreadsheet ID (from the URL)
        credentials_file: Path to Google Service Account JSON credentials
    """
    try:
        # Define the scope
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate using service account
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet by ID
        if not spreadsheet_id:
            raise ValueError("spreadsheet_id is required")
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ Opened existing spreadsheet")
        
        # Get the first worksheet (or create if doesn't exist)
        try:
            worksheet = spreadsheet.sheet1
        except:
            worksheet = spreadsheet.add_worksheet(title="Sheet1", rows=1000, cols=20)
        
        # Clear existing data
        worksheet.clear()
        
        # Prepare data for batch update
        sheet_data = [fieldnames]  # Header row
        
        for row in data_rows:
            sheet_row = [row.get(field, '') for field in fieldnames]
            sheet_data.append(sheet_row)
        
        # Write data to sheet
        worksheet.update('A1', sheet_data)
        
        # Format header row (bold)
        worksheet.format('A1:K1', {'textFormat': {'bold': True}})
        
        print(f"\n✅ Successfully wrote {len(data_rows)} rows to Google Sheets!")
        print(f"📊 Spreadsheet URL: {spreadsheet.url}")
        
        return spreadsheet.url
        
    except FileNotFoundError:
        print(f"\n❌ Error: Credentials file '{credentials_file}' not found.")
        print("Please create a Google Service Account and download the credentials JSON file.")
        return None
    except Exception as e:
        print(f"\n❌ Error writing to Google Sheets: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return None


def append_to_google_sheets(data_rows, fieldnames, spreadsheet_id, credentials_file="credentials.json", sheet_name=None):
    """
    Append data to Google Sheets without clearing existing content.
    
    Args:
        data_rows: List of dictionaries containing row data
        fieldnames: List of column headers
        spreadsheet_id: Google Sheets spreadsheet ID
        credentials_file: Path to Google Service Account JSON credentials
        sheet_name: Name of the sheet to append to (with timestamp)
    """
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get or create the worksheet with the given sheet name
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            # Add headers to the new sheet
            worksheet.append_row(fieldnames)
            worksheet.format('A1:K1', {'textFormat': {'bold': True}})
        
        # Prepare rows to append
        rows_to_append = []
        for row in data_rows:
            sheet_row = [row.get(field, '') for field in fieldnames]
            rows_to_append.append(sheet_row)
        
        # Append rows to the sheet
        if rows_to_append:
            worksheet.append_rows(rows_to_append)
            print(f"  ✅ Added {len(rows_to_append)} rows to sheet '{sheet_name}'")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ Error appending to Google Sheets: {e}")
        print(f"  Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


def initialize_google_sheet(fieldnames, spreadsheet_id, credentials_file="credentials.json", sheet_name=None):
    """
    Initialize Google Sheet by creating or getting a timestamped sheet and adding headers.
    
    Args:
        fieldnames: List of column headers
        spreadsheet_id: Google Sheets spreadsheet ID
        credentials_file: Path to Google Service Account JSON credentials
        sheet_name: Name of the sheet with timestamp (e.g., 2026-03-03_0930)
    """
    try:
        # Check if credentials file exists
        if not os.path.exists(credentials_file):
            print(f"❌ Credentials file not found: {credentials_file}")
            print(f"   Current directory: {os.getcwd()}")
            return False
        
        # Load credentials to get service account email
        import json
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
            service_email = creds_data.get('client_email', 'Unknown')
        
        print(f"📧 Service Account: {service_email}")
        print(f"   Make sure this email has Editor access to your Google Sheet!")
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get or create the worksheet with the timestamped name
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            print(f"✅ Using existing sheet: '{sheet_name}'")
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            print(f"✅ Created new sheet: '{sheet_name}'")
            
            # Add header to the new sheet
            worksheet.append_row(fieldnames)
            worksheet.format('A1:K1', {'textFormat': {'bold': True}})
        
        print(f"📊 Spreadsheet URL: {spreadsheet.url}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Google Sheets: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


def classify_signal(ltp, close, oi_change):
    """
    OI + Price Action Signal Classification for PE options.
    Compares current LTP vs previous day close and OI direction.

    | Price      | OI       | Signal                          |
    |------------|----------|---------------------------------|
    | Rising     | Rising   | Long Buildup                    |
    | Falling    | Rising   | Short Buildup ⚠️  (Most Bearish) |
    | Rising     | Falling  | Short Covering                  |
    | Falling    | Falling  | Long Unwinding                  |
    """
    if ltp is None or close is None or close == 0 or oi_change is None:
        return "N/A"

    price_up = ltp >= close
    oi_up    = oi_change > 0

    if price_up and oi_up:
        return "Long Buildup"
    elif not price_up and oi_up:
        return "Short Buildup ⚠️"
    elif price_up and not oi_up:
        return "Short Covering"
    else:
        return "Long Unwinding"


def process_symbol(symbol, api, fno_df, underlying_ltp_cache, fieldnames):
    """
    Process a single symbol and return all its option data.
    This function is designed to be called in parallel.
    """
    import re
    from datetime import datetime
    
    symbol_data = []
    
    try:
        # 1. Fetch LTP for the underlying stock
        underlying_quote = api.get_quote(
            trading_symbol=symbol,
            exchange="NSE",
            segment="CASH"
        )
        underlying_ltp = underlying_quote.get('last_price')
        if underlying_ltp is None:
            return symbol_data
        
        # Cache the underlying LTP
        underlying_ltp_cache[symbol] = underlying_ltp

        # 2. Filter PE options for this underlying
        stock_options = fno_df[fno_df['trading_symbol'].str.startswith(symbol.upper())]

        if stock_options.empty:
            return symbol_data

        for _, row in stock_options.iterrows():
            ts = row['trading_symbol']
            # e.g. RELIANCE26MAR2600PE
            match = re.search(r'(\d+[A-Z]{3})(\d+)(PE)$', ts)
            if not match:
                continue

            expiry_str = match.group(1)
            if 'MAR' not in expiry_str.upper():
                continue  # Only include 30 March expiry

            strike    = float(match.group(2))
            opt_type  = match.group(3)  # Always 'PE'

            # Apply 5% Filtering Logic - PE only (strike <= 95% of underlying)
            keep = strike <= (underlying_ltp * 0.95)

            if keep:
                try:
                    quote = api.get_quote(
                        trading_symbol=ts,
                        exchange=row['exchange'],
                        segment=row['segment']
                    )
                    
                    # Delay to avoid rate limiting (0.2s with 4 workers = ~10 req/sec per API)
                    time.sleep(0.20)

                    oi = quote.get('open_interest', 0)
                    if oi == 0:
                        continue  # Skip if OI is 0

                    ltp       = quote.get('last_price')
                    close     = quote.get('close')       # Previous day close
                    oi_change = quote.get('oi_day_change')

                    # ── OI Change % ──────────────────────────────────────
                    # prev_oi = today's OI minus today's change
                    prev_oi = (oi - oi_change) if (oi_change is not None) else None
                    if prev_oi and prev_oi > 0:
                        oi_change_pct = round((oi_change / prev_oi) * 100, 2)
                    else:
                        oi_change_pct = "N/A"

                    # Map fields
                    last_trade_time = quote.get('last_trade_time')
                    date_str = (
                        datetime.fromtimestamp(last_trade_time).strftime('%Y-%m-%d %H:%M:%S')
                        if last_trade_time else "N/A"
                    )

                    # Calculate Vol/OI Ratio
                    volume = quote.get('volume', 0)
                    vol_oi_ratio = round(volume / oi, 4) if oi > 0 else "N/A"

                    row_data = {
                        'Date'            : date_str,
                        'Symbol'          : symbol,
                        'Expiry'          : expiry_str,
                        'Strike'          : strike,
                        'Type'            : opt_type,
                        'LTP'             : ltp,
                        'Volume'          : volume,
                        'OI'              : oi,
                        'OI Change %'     : oi_change_pct,
                        'Vol/OI Ratio'    : vol_oi_ratio,
                        'Underlying Value': underlying_ltp
                    }

                    symbol_data.append(row_data)

                    oi_pct_display = f"{oi_change_pct}%" if oi_change_pct != "N/A" else "N/A"
                    print(
                        f"{symbol:<15} | {strike:<10} | {str(ltp):<8} | "
                        f"{oi:<12} | {oi_pct_display:<10}"
                    )

                except Exception:
                    continue

    except Exception as e:
        print(f"Error processing {symbol}: {e}")
    
    return symbol_data


def fetch_live_oi():
    # User's Watchlist
    watchlist = [
        "360ONE", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ALKEM", "AMBER",
        "ANGELONE", "APLAPOLLO", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY",
        "ASTRAL", "ATGL", "AUBANK", "AUROPHARMA", "BAJAJ-AUTO", "BAJAJFINSV",
        "BAJAJHLDNG", "BAJFINANCE", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK",
        "BANKBARODA", "BANKINDIA", "BDL", "BERGEPAINT", "BHARATFORG",
        "BHARTIARTL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BPCL", "BRITANNIA",
        "BSE", "CAMS", "CANBK", "CANFINHOME", "CDSL", "CESC",
        "CGPOWER", "CHAMBLFERT", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE",
        "COLPAL", "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", "DABUR",
        "DALBHARAT", "DEEPAKNTR", "DELHIVERY", "DIVISLAB", "DIXON", "DLF",
        "DMART", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", "FEDERALBNK",
         "GAIL", "GLENMARK", "GMRINFRA", "GODREJCP",
        "GODREJPROP", "GRASIM", "GUJGASLTD", "HAL", "HAVELLS", "HCLTECH",
        "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO",
        "HINDUNILVR", "HINDZINC", "HUDCO", "ICICIGI", "ICICIPRULI", "IDFC",
        "IDFCFIRSTB", "IEX", "IGL", "IIFL", "INDHOTEL", "INDIACEM", "INDIAMART",
        "INDIGO", "INDUSINDBK", "INDUSTOWER", "INOXWIND", "IOC", "IPCALAB",
        "IREDA", "IRFC", "JINDALSTEL", "JIOFIN", "JKCEMENT", "JSWENERGY",
        "JSWSTEEL", "JUBLFOOD", "KAYNES", "KFINTECH", "L&TFH",
        "LALPATHLAB", "LICHSGFIN", "LICI", "LODHA", "LT", "LTIM", "LTTS",
        "LUPIN", "M&M", "M&MFIN", "MANAPPURAM", "MANKIND", "MARICO", "MAZDOCK",
        "MCX", "METROPOLIS", "MFSL", "MGL", "MOTHERSON", "MPHASIS", "MUTHOOTFIN",
        "NATIONALUM", "NAVINFLUOR", "NBCC", "NESTLEIND", "NHPC", "NMDC", "NTPC",
        "NUVAMA", "OBEROIRLTY", "OFSS", "ONGC", "PAGEIND", "PATANJALI", "PEL",
        "PERSISTENT", "PETRONET", "PFC", "PGEL", "PGHH", "PHOENIXLTD",
        "PIDILITIND", "PIIND", "PNB", "PNBHOUSING", "POLYCAB", "POWERGRID",
        "POWERINDIA", "PPLPHARMA", "PREMIERENE", "PVRINOX", "RAMCOCEM",
        "RBLBANK", "RECLTD", "RVNL", "SAIL", "SAMMAANCAP", "SBICARD", "SBILIFE",
        "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SRF",
        "SUNPHARMA", "SUNTV", "SUZLON", "SWIGGY", "SYNGENE", "TATACHEM",
        "TATACOMM", "TATACONSUM", "TATAELXSI", "TATAPOWER", "TATASTEEL",
        "TATATECH", "TECHM", "TITAGARH", "TORNTPHARM", "TORNTPOWER", "TRENT",
        "TVSMOTOR", "UBL", "ULTRACEMCO", "UNITDSPR", "UNOMINDA", "UPL", "VBL",
        "VEDL", "VOLTAS", "WAAREEENER", "YESBANK", "ZEEL", "ETERNAL"
    ]

    # Normalize watchlist for case-insensitive matching
    watchlist_set = set(s.upper() for s in watchlist)

    creds_list = get_credentials()  # Reads from .env or environment variables

    if not creds_list or len(creds_list) == 0:
        print("Missing API credentials. Please check .env file or set environment variables.")
        return

    # Create API instances for all credentials
    apis = []
    for i, creds in enumerate(creds_list, 1):
        try:
            print(f"Obtaining access token for API #{i}...")
            access_token = GrowwAPI.get_access_token(
                api_key=creds['api_key'],
                secret=creds['secret']
            )
            api_instance = GrowwAPI(token=access_token)
            apis.append(api_instance)
            print(f"✅ Access token #{i} obtained successfully.")
        except Exception as e:
            print(f"❌ Error obtaining token for API #{i}: {e}")

    if not apis:
        print("Failed to create any API instances.")
        return

    try:
        print("Loading instruments (this may take a moment)...")
        all_inst = apis[0].get_all_instruments()  # Use first API to get instruments list

        # Filter for NSE FNO instruments that match the watchlist - PE only
        fno_df = all_inst[
            (all_inst['exchange'] == 'NSE') &
            (all_inst['segment'] == 'FNO') &
            (all_inst['instrument_type'] == 'PE') &
            (all_inst['underlying_symbol'].str.upper().isin(watchlist_set))
        ]

        if fno_df.empty:
            print("No matching F&O PE instruments found for the watchlist.")
            return

        print(f"Found {len(fno_df)} total F&O PE instruments.")

        csv_filename = "GROWW_OI_Export.csv"
        fieldnames = [
            'Date', 'Symbol', 'Expiry', 'Strike', 'Type',
            'LTP', 'Volume', 'OI', 'OI Change %', 'Vol/OI Ratio',
            'Underlying Value'
        ]

        import csv
        from datetime import datetime
        import re

        # Generate timestamped sheet name (e.g., 2026-03-03_0930)
        sheet_name = get_sheet_name_with_timestamp()
        
        # Initialize Google Sheet with headers
        SPREADSHEET_ID = "1iGiZxhDXZRzHegcJtee5twNM0TzC3kTtEPRyabykuRs"
        CREDENTIALS_FILE = "credentials.json"
        
        print(f"📊 Initializing Google Sheet...")
        sheets_available = initialize_google_sheet(fieldnames, SPREADSHEET_ID, CREDENTIALS_FILE, sheet_name)
        
        if not sheets_available:
            print("\n⚠️ Google Sheets not available - continuing with CSV only...")
            print("   (Data will still be saved to CSV file)\n")

        # Collect all rows first
        all_data_rows = []
        batch_data = []  # For batching updates every 5 symbols
        symbols_processed = 0
        underlying_ltp_cache = {}  # Cache for underlying LTPs
        
        print(f"Processing watchlist with 5 parallel workers (30MAR expiry)...")
        print(f"{'Symbol':<15} | {'Strike':<10} | {'LTP':<8} | {'OI':<12} | {'OI Chg%':<10}")
        print("-" * 80)

        # Process symbols in parallel with 4 workers (2 per API for load balancing)
        num_workers = min(4, len(apis) * 2)  # Scale workers based on number of APIs
        print(f"Using {len(apis)} API key(s) with {num_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all symbol processing tasks, distributing across APIs
            future_to_symbol = {}
            for idx, symbol in enumerate(watchlist):
                api_to_use = apis[idx % len(apis)]  # Round-robin distribution
                future = executor.submit(process_symbol, symbol, api_to_use, fno_df, underlying_ltp_cache, fieldnames)
                future_to_symbol[future] = symbol
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    symbol_data = future.result()
                    
                    # Add all rows from this symbol
                    if symbol_data:
                        all_data_rows.extend(symbol_data)
                        batch_data.extend(symbol_data)
                    
                    # Increment symbol counter and write to Sheets every 5 symbols
                    symbols_processed += 1
                    if sheets_available and symbols_processed % 5 == 0 and batch_data:
                        try:
                            append_to_google_sheets(batch_data, fieldnames, SPREADSHEET_ID, CREDENTIALS_FILE, sheet_name)
                        except Exception as e:
                            print(f"  ⚠️ Skipping Google Sheets update: {e}")
                        batch_data = []  # Clear batch after writing
                        
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
        
        # Write any remaining batch data to Google Sheets
        if sheets_available and batch_data:
            print(f"\n📄 Writing final batch to Google Sheets...")
            try:
                append_to_google_sheets(batch_data, fieldnames, SPREADSHEET_ID, CREDENTIALS_FILE, sheet_name)
            except Exception as e:
                print(f"  ⚠️ Could not write final batch: {e}")
        
        # Write collected data to CSV
        print(f"\n💾 Writing {len(all_data_rows)} rows to CSV: {csv_filename}...")
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data_rows)
        print(f"✅ Data saved to {csv_filename}")
        
        if sheets_available:
            print(f"✅ Total {len(all_data_rows)} rows synced to Google Sheets!")
            print(f"   📅 Sheet name: {sheet_name} (Date + Time)")
        else:
            print(f"ℹ️ Google Sheets sync was skipped (permission issue). Data saved to CSV only.")
        
        print("\n📊 OI Change % shows how aggressively positions are being built or unwound.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    fetch_live_oi()