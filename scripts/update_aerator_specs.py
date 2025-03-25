import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import subprocess
import os
import time
from datetime import datetime

# Configuration
CREDENTIALS_FILE = "/home/luisvinatea/Dev/Repos/Aquaculture/.credentials/aquacyclone-0b87afb205f8.json"
SPREADSHEET_ID = "1ou6ZOpV1UrIHpPU9ith1_1YLpvXG3NbYMSqYIpfCkKw"
CSV_FILE = "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/csv/Pesos_WangFa_Beraqua_3HP_2025-03-22.csv"
SHEET_NAME = "Pesos"
TIMESTAMP_FILE = "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/csv/last_sync_timestamp.txt"

def get_sheets_service():
    """Authenticate and return the Google Sheets API service."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    return service

def get_sheet_dimensions(service, spreadsheet_id, sheet_name):
    """Get the dimensions (last row and last column) of the sheet."""
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get("sheets", [])
    sheet = next(s for s in sheets if s["properties"]["title"] == sheet_name)
    grid_properties = sheet["properties"]["gridProperties"]
    last_row = grid_properties.get("rowCount", 1)
    last_column = grid_properties.get("columnCount", 1)

    # Get the actual last row and column with data
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1:ZZ{last_row}"
    ).execute()
    values = result.get("values", [])
    if not values:
        return 1, 1

    actual_last_row = len(values)
    actual_last_column = max(len(row) for row in values) if values else 1
    return actual_last_row, actual_last_column

def read_csv_to_list(csv_file):
    df = pd.read_csv(csv_file)
    data = [df.columns.tolist()] + df.values.tolist()
    # Replace NaN with empty string in the resulting list
    for row in data:
        for i, value in enumerate(row):
            if pd.isna(value):  # Checks for NaN or None
                row[i] = ""
    return data

def write_list_to_csv(data, csv_file):
    """Write a list of lists to the CSV file."""
    df = pd.DataFrame(data[1:], columns=data[0])
    df.to_csv(csv_file, index=False)
    print(f"Updated {csv_file} with {len(data)} rows.")

def read_google_sheet(service, spreadsheet_id, sheet_name, last_row, last_column):
    """Read data from the specified range in the Google Sheet."""
    # Convert last_column to a letter (e.g., 10 -> J)
    col_letter = chr(64 + last_column) if last_column <= 26 else "ZZ"
    range_name = f"{sheet_name}!A1:{col_letter}{last_row}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get("values", [])
    return values

def update_google_sheet(service, spreadsheet_id, sheet_name, new_data):
    last_row, last_column = get_sheet_dimensions(service, spreadsheet_id, sheet_name)
    existing_data = read_google_sheet(service, spreadsheet_id, sheet_name, last_row, last_column)
    
    if not existing_data:
        merged_data = new_data
    else:
        # Assume first column (A) is a unique key (e.g., brand)
        existing_dict = {row[0]: row for row in existing_data[1:]}  # Skip header
        new_dict = {row[0]: row for row in new_data[1:]}
        # Merge, prioritizing new_data for existing keys
        merged_dict = {**existing_dict, **new_dict}
        # Rebuild data with headers
        merged_data = [new_data[0]] + list(merged_dict.values())
        # Ensure all rows match the widest column count
        max_cols = max(len(new_data[0]), len(existing_data[0]))
        for row in merged_data:
            while len(row) < max_cols:
                row.append("")
    
    col_letter = chr(64 + len(merged_data[0])) if merged_data else "ZZ"
    range_name = f"{sheet_name}!A1:{col_letter}{len(merged_data)}"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": merged_data}
    ).execute()
    print(f"Updated {range_name} with {len(merged_data)} rows.")

def get_last_sync_timestamp():
    """Read the last sync timestamp from the file."""
    if os.path.exists(TIMESTAMP_FILE):
        with open(TIMESTAMP_FILE, "r") as f:
            return float(f.read().strip())
    return 0

def save_last_sync_timestamp():
    """Save the current timestamp to the file."""
    with open(TIMESTAMP_FILE, "w") as f:
        f.write(str(time.time()))

def check_git_status(csv_file):
    """Check if the CSV file has uncommitted changes in Git."""
    try:
        repo_dir = os.path.dirname(os.path.dirname(csv_file))
        os.chdir(repo_dir)
        result = subprocess.run(
            ["git", "status", "--porcelain", csv_file],
            capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error checking Git status: {e}")
        return False

def commit_csv_changes(csv_file, message="Auto-commit during sync"):
    """Commit changes to the CSV file in Git."""
    try:
        repo_dir = os.path.dirname(os.path.dirname(csv_file))
        os.chdir(repo_dir)
        subprocess.run(["git", "add", csv_file], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        print(f"Committed changes to {csv_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error committing changes: {e}")

def pull_from_google_sheet():
    """Pull data from the Google Sheet and update the local CSV."""
    service = get_sheets_service()
    last_row, last_column = get_sheet_dimensions(service, SPREADSHEET_ID, SHEET_NAME)
    sheet_data = read_google_sheet(service, SPREADSHEET_ID, SHEET_NAME, last_row, last_column)

    if not sheet_data:
        print("No data found in Google Sheet.")
        return

    write_list_to_csv(sheet_data, CSV_FILE)
    commit_csv_changes(CSV_FILE, "Pulled changes from Google Sheet")
    save_last_sync_timestamp()

def push_to_google_sheet():
    """Push data from the local CSV to the Google Sheet."""
    if check_git_status(CSV_FILE):
        print("Uncommitted changes detected in the CSV. Committing before pushing...")
        commit_csv_changes(CSV_FILE, "Auto-commit before pushing to Google Sheet")

    csv_data = read_csv_to_list(CSV_FILE)
    service = get_sheets_service()
    update_google_sheet(service, SPREADSHEET_ID, SHEET_NAME, csv_data)
    save_last_sync_timestamp()

def sync():
    has_local_changes = check_git_status(CSV_FILE)
    service = get_sheets_service()
    last_row, last_column = get_sheet_dimensions(service, SPREADSHEET_ID, SHEET_NAME)
    sheet_data = read_google_sheet(service, SPREADSHEET_ID, SHEET_NAME, last_row, last_column)
    csv_data = read_csv_to_list(CSV_FILE)

    if sheet_data != csv_data:
        print("Conflict detected: Google Sheet and local CSV have diverged.")
        if has_local_changes:
            print("Local CSV has uncommitted changes. Please commit or stash them before syncing.")
            return
        if not sheet_data and csv_data:
            print("Google Sheet is empty. Pushing local CSV data instead of pulling...")
            push_to_google_sheet()
        else:
            print("Pulling changes from Google Sheet...")
            pull_from_google_sheet()
    else:
        if has_local_changes:
            print("Pushing local changes to Google Sheet...")
            push_to_google_sheet()
        else:
            print("No changes to sync.")

def pull():
    pull_from_google_sheet()

def push():
    push_to_google_sheet()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "pull":
            pull()
        elif sys.argv[1] == "push":
            push()
        else:
            sync()
    else:
        sync()