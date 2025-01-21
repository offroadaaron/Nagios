#!/usr/bin/python3
#./nsx_backup_check.py --nsx-manager <NSX_MANAGER_URL> --credential-file <CREDENTIALS_FILE_PATH> --time-period <TIME_PERIOD_IN_HOURS>
  
import requests
import json
import sys
from datetime import datetime, timedelta
import urllib3
import argparse

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Define the command-line arguments
parser = argparse.ArgumentParser(description='NSX Backup Check')
parser.add_argument('--nsx-manager', required=True, help='NSX Manager URL')
parser.add_argument('--credential-file', required=True, help='Path to the credentials file')
parser.add_argument('--time-period', type=int, required=True, help='Time period in hours')

# Parse the command-line arguments
args = parser.parse_args()

# Set the NSX Manager URL
nsx_manager = args.nsx_manager

# Set the path to the credentials file
credentials_file = args.credential_file

# Set the time period
time_period_in_hours = args.time_period

# Read the credentials from the file
try:
    with open(credentials_file, 'r') as f:
        lines = f.readlines()
        if len(lines)!= 2:
            print(f"Invalid credentials file format. Expected 2 lines: username and password.")
            exit(2)
        nsx_username = lines[0].strip()
        nsx_password = lines[1].strip()
except FileNotFoundError:
    print(f"Credentials file {credentials_file} not found")
    exit(2)

# Get the backup status
backup_url = nsx_manager + '/policy/api/v1/cluster/backups/overview'
response = requests.get(backup_url, auth=(nsx_username, nsx_password), verify=False)
if response.status_code!= 200:
    print(f"HTTP Error {response.status_code}: {response.reason}")
    print(response.text)
    exit(2)

# Check the backup status
backup_data = response.json()
if 'backup_operation_history' in backup_data and 'cluster_backup_statuses' in backup_data['backup_operation_history']:
    cluster_backup_statuses = backup_data['backup_operation_history']['cluster_backup_statuses']
    recent_backups = [backup for backup in cluster_backup_statuses if (datetime.now() - datetime.fromtimestamp(backup['start_time'] / 1000)).total_seconds() / 3600 <= time_period_in_hours]
    if recent_backups:
        print(f"OK - Found {len(recent_backups)} backups within the last {time_period_in_hours} hours")
        for backup in recent_backups:
            print(f"Backup ID: {backup['backup_id']}, Start Time: {datetime.fromtimestamp(backup['start_time'] / 1000)}, End Time: {datetime.fromtimestamp(backup['end_time'] / 1000)}")
        exit(0)
    else:
        last_backup = min(cluster_backup_statuses, key=lambda x: abs(datetime.now() - datetime.fromtimestamp(x['start_time'] / 1000)))
        last_backup_time = datetime.fromtimestamp(last_backup['start_time'] / 1000)
        time_since_last_backup = (datetime.now() - last_backup_time).total_seconds() / 3600
        print(f"CRITICAL - No backups found within the last {time_period_in_hours} hours. Last backup was {time_since_last_backup:.2f} hours ago on {last_backup_time}")
        exit(2)
else:
    print(f"UNKNOWN - Failed to retrieve backup status")
    exit(3)
