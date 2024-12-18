#!/usr/bin/env python3

import http.client
import ssl
import json
import sys
import base64

def fetch_alarms(api_url, username, password, verify_ssl=False):
    if verify_ssl:
        context = ssl.create_default_context()
    else:
        context = ssl._create_unverified_context()

    conn = http.client.HTTPSConnection(api_url, context=context)
    headers = {
        'Authorization': f'Basic {get_auth_header(username, password)}',
        'Content-Type': 'application/json'
    }

    try:
        conn.request("GET", "/api/v1/alarms", headers=headers)
        response = conn.getresponse()
        if response.status == 200:
            data = response.read().decode('utf-8')
            return json.loads(data)
        else:
            print(f"UNKNOWN: API request failed with status {response.status}")
            sys.exit(3)
    finally:
        conn.close()

def get_auth_header(username, password):
    auth = f"{username}:{password}"
    auth_bytes = auth.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    return auth_base64

def read_credentials_from_file(creds_file):
    try:
        with open(creds_file, 'r') as file:
            lines = file.readlines()
            if len(lines) != 2:
                print("UNKNOWN: Credentials file should contain exactly two lines: username and password")
                sys.exit(3)
            username = lines[0].strip()
            password = lines[1].strip()
            return username, password
    except FileNotFoundError:
        print(f"UNKNOWN: Credentials file {creds_file} not found")
        sys.exit(3)
    except Exception as e:
        print(f"UNKNOWN: Error reading credentials file: {e}")
        sys.exit(3)

def process_alarms(alarms):
    critical_alarms = []
    warning_alarms = []
    ok_alarms = []

    for alarm in alarms.get('results', []):
        if alarm['status'] == 'OPEN':
            if alarm['severity'] == 'CRITICAL':
                critical_alarms.append(alarm)
            elif alarm['severity'] in ['HIGH', 'MEDIUM']:
                warning_alarms.append(alarm)
            else:
                ok_alarms.append(alarm)
        else:
            ok_alarms.append(alarm)

    # Debug prints
    print(f"Critical Alarms: {len(critical_alarms)}")
    print(f"Warning Alarms: {len(warning_alarms)}")
    print(f"OK Alarms: {len(ok_alarms)}")

    if critical_alarms:
        output_critical(critical_alarms, warning_alarms)
    elif warning_alarms:
        output_warning(warning_alarms)
    else:
        output_ok()

def output_critical(critical_alarms, warning_alarms):
    print("CRITICAL: Open critical alarms found")
    for alarm in critical_alarms:
        print(f" - ID: {alarm['id']}, Severity: {alarm['severity']}, Summary: {alarm['summary']}, Description: {alarm['description']}")

    if warning_alarms:
        print(" - Warning Alarms:")
        for alarm in warning_alarms:
            print(f"   - ID: {alarm['id']}, Severity: {alarm['severity']}, Summary: {alarm['summary']}, Description: {alarm['description']}")

    sys.exit(2)

def output_warning(warning_alarms):
    print("WARNING: Open warning alarms found")
    for alarm in warning_alarms:
        print(f" - ID: {alarm['id']}, Severity: {alarm['severity']}, Summary: {alarm['summary']}, Description: {alarm['description']}")
    sys.exit(1)

def output_ok():
    print("OK: No open critical or high/medium alarms found")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: check_nsx_alarms.py <CREDENTIALS_FILE> <API_URL>")
        sys.exit(3)

    creds_file = sys.argv[1]
    NSX_API_URL = sys.argv[2]

    username, password = read_credentials_from_file(creds_file)

    alarms = fetch_alarms(NSX_API_URL, username, password)
    process_alarms(alarms)
