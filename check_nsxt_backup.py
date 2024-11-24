#!/usr/bin/env python3
"""
Nagios check to monitor NSX-T backup status
Florian Grehl - www.virten.net

usage: check_nsxt_backup.py [-h] -n NSX_HOST [-t TCP_PORT] -u USER -p PASSWORD
                            [-i] [-a MAX_AGE]
"""

import requests
import urllib3
import argparse
import json
from datetime import datetime
from time import time
import sys

def getargs():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-n', '--nsx_host', type=str, required=True, help='NSX-T Manager host')
    arg_parser.add_argument('-t', '--tcp_port', type=int, default=443, help='NSX-T Manager TCP port')
    arg_parser.add_argument('-u', '--user', type=str, required=True, help='NSX-T user')
    arg_parser.add_argument('-p', '--password', type=str, required=True, help='Password')
    arg_parser.add_argument('-i', '--insecure', default=False, action='store_true', help='Ignore SSL errors')
    arg_parser.add_argument('-a', '--max_age', type=int, default=24, help='Backup maximum age (hours)')
    parser = arg_parser
    args = parser.parse_args()
    return args

def main():
    args = getargs()
    session = requests.session()

    # Disable server certificate verification.
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False

    session.auth = (args.user, args.password)
    response = session.get(f'https://{args.nsx_host}/api/v1/cluster/backups/history')

    if response.status_code != 200:
        print('Could not connect to NSX-T')
        sys.exit(2)

    data = response.json()  # Parse JSON response
    now = int(time())  # Get the current time in seconds
    error = False

    # Iterate over the backup data
    for key, value in data.items():
        if isinstance(value, list):  # Check if value is a list
            first_item = value[0]  # Get the first item in the list
            end_time = first_item.get('end_time', 0)  # Safely get 'end_time'
            success = first_item.get('success', False)  # Safely get 'success'

            # Calculate the age of the backup in hours
            age_in_hours = (now - (end_time / 1000)) / 3600  # Convert from milliseconds to hours
            if age_in_hours > args.max_age:
                print(f'NSX-T {key.replace("_backup_statuses", "")} backup is too old ({int(age_in_hours)} hours)')
                error = True

            if not success:
                print(f'NSX-T {key.replace("_backup_statuses", "")} backup failed')
                error = True

        elif isinstance(value, dict):  # Check if value is a dictionary (e.g., `overall_backup_status`)
            # Handle cases where the value is a dictionary
            end_time = value.get('end_time', 0)  # Get 'end_time'

            # Calculate the age of the backup in hours
            age_in_hours = (now - (end_time / 1000)) / 3600  # Convert from milliseconds to hours
            if age_in_hours > args.max_age:
                print(f'NSX-T {key.replace("_backup_statuses", "")} backup is too old ({int(age_in_hours)} hours)')
                error = True

        elif isinstance(value, str):  # Handle string data types (e.g., `overall_backup_status`)
            # Ignore or log string data (e.g., `overall_backup_status`)
            # No error message needed for this case; just skip or log if necessary
            # You can add custom logging or handling here, but we're just skipping it.
            pass

        else:  # Handle the case where 'value' is neither a list, dictionary, nor string
            print(f"Unexpected data format for {key}: {type(value).__name__}. Expected a list or dictionary.")
            error = True

    if error:
        sys.exit(2)
    else:
        print('OK')

if __name__ == "__main__":
    main()

