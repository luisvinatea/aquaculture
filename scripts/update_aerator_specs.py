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
CSV_FILE = "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/Pesos_WangFa_Beraqua_3HP_2025-03-22.csv"
SHEET_NAME = "Pesos"
RANGE_NAME = "A1:I100"
TIMESTAMP_FILE = "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/last_sync_timestamp.txt"

def get_sheets_service():
    """Authenticate and return the Google Sheets API service."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    return service

def read_csv_to_list(csv_file):
    """Read the CSV file and return the data as a list of lists."""
    df = pd.read_csv(csv_file)
    return [df.columns.tolist()] + df.values.tolist()

def write_list_to_csv(data, csv_file):
    """Write a list of lists to the CSV file."""
    df = pd.DataFrame(data[1:], columns=data[0])
    df.to_csv(csv_file, index=False)
    print(f"Updated {csv_file} with {len(data)} rows.")

def read_google_sheet(service, spreadsheet_id, sheet_name, range_name):
    """Read data from the specified range in the Google Sheet."""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{range_name}"
    ).execute()
    values = result.get("values", [])
    return values

def update_google_sheet(service, spreadsheet_id, sheet_name, range_name, data):
    """Update the specified range in the Google Sheet with the provided data."""
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{range_name}",
        body={}
    ).execute()
    body = {"values": data}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{range_name}",
        valueInputOption="RAW",
        body=body
    ).execute()
    print(f"Updated {sheet_name}!{range_name} with {len(data)} rows.")

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
        # Change to the repository directory
        repo_dir = os.path.dirname(os.path.dirname(csv_file))
        os.chdir(repo_dir)
        # Check if the file is modified
        result = subprocess.run(
            ["git", "status", "--porcelain", csv_file],
            capture_output=True, text=True
        )
        return bool(result.stdout.strip())  # Returns True if there are uncommitted changes
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
    sheet_data = read_google_sheet(service, SPREADSHEET_ID, SHEET_NAME, RANGE_NAME)

    if not sheet_data:
        print("No data found in Google Sheet.")
        return

    # Write the data to the CSV
    write_list_to_csv(sheet_data, CSV_FILE)

    # Commit the changes to Git
    commit_csv_changes(CSV_FILE, "Pulled changes from Google Sheet")
    save_last_sync_timestamp()

def push_to_google_sheet():
    """Push data from the local CSV to the Google Sheet."""
    # Check for uncommitted changes
    if check_git_status(CSV_FILE):
        print("Uncommitted changes detected in the CSV. Committing before pushing...")
        commit_csv_changes(CSV_FILE, "Auto-commit before pushing to Google Sheet")

    # Read the CSV and update the Google Sheet
    csv_data = read_csv_to_list(CSV_FILE)
    service = get_sheets_service()
    update_google_sheet(service, SPREADSHEET_ID, SHEET_NAME, RANGE_NAME, csv_data)
    save_last_sync_timestamp()

def sync():
    """Perform a bidirectional sync with conflict detection."""
    # Check if the CSV has uncommitted changes
    has_local_changes = check_git_status(CSV_FILE)

    # Check if the Google Sheet has been edited since the last sync
    service = get_sheets_service()
    sheet_data = read_google_sheet(service, SPREADSHEET_ID, SHEET_NAME, RANGE_NAME)
    csv_data = read_csv_to_list(CSV_FILE)

    # Simple conflict detection: Compare the data
    # This is a basic check; you can enhance it based on your needs
    if sheet_data != csv_data:
        print("Conflict detected: Google Sheet and local CSV have diverged.")
        if has_local_changes:
            print("Local CSV has uncommitted changes. Please commit or stash them before syncing.")
            return

        # Pull from Google Sheet (Google Sheet takes precedence in this simple model)
        print("Pulling changes from Google Sheet...")
        pull_from_google_sheet()
    else:
        # No conflict, push local changes if any
        if has_local_changes:
            print("Pushing local changes to Google Sheet...")
            push_to_google_sheet()
        else:
            print("No changes to sync.")

def main():
    sync()

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