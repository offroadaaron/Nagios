#!/usr/bin/python3
import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
import urllib.request
import urllib.parse

logging.basicConfig(level=logging.INFO)

def get_token(url, username, password):
    headers = {
        'accept': 'application/json',
        'x-api-version': '1.2-rev0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = urllib.parse.urlencode({
        'grant_type': 'password',
        'username': username,
        'password': password
    })
    try:
        req = urllib.request.Request(f'{url}/api/oauth2/token', data=data.encode('utf-8'), headers=headers)
        response = urllib.request.urlopen(req)
        token_response = json.loads(response.read().decode('utf-8'))
        return token_response['access_token']
    except Exception as e:
        print(f"CRITICAL: Failed to get token: {e}")
        sys.exit(2)

def get_restore_points(url, token):
    headers = {
        'accept': 'application/json',
        'x-api-version': '1.2-rev0',
        'Authorization': f'Bearer {token}'
    }
    try:
        req = urllib.request.Request(f'{url}/api/v1/restorePoints', headers=headers)
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"CRITICAL: Failed to get restore points: {e}")
        sys.exit(2)

def get_backup_status(url, token, backup_id):
    headers = {
        'accept': 'application/json',
        'x-api-version': '1.2-rev0',
        'Authorization': f'Bearer {token}'
    }
    try:
        req = urllib.request.Request(f'{url}/api/v1/backups/{backup_id}', headers=headers)
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"CRITICAL: Failed to get backup status: {e}")
        sys.exit(2)

def read_credentials(credentials_file):
    try:
        with open(credentials_file, 'r') as f:
            lines = f.readlines()
            if len(lines)!= 2:
                print(f"CRITICAL: Invalid credentials file format. Expected 2 lines: username and password")
                sys.exit(2)
            username = lines[0].strip()
            password = lines[1].strip()
            return username, password
    except FileNotFoundError:
        print(f"CRITICAL: Credentials file {credentials_file} not found")
        sys.exit(2)

def main():
    parser = argparse.ArgumentParser(description='Check Veeam restore points')
    parser.add_argument('--url', help='Veeam server URL', required=True)
    parser.add_argument('--credentials_file', help='Path to credentials file', required=True)
    parser.add_argument('--vm_name', help='Name of the VM to check', required=True)
    parser.add_argument('--max_backup_age', help='Maximum allowed backup age in hours', required=True, type=int)
    args = parser.parse_args()

    # Suppress HTTPS warnings
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

    username, password = read_credentials(args.credentials_file)
    token = get_token(args.url, username, password)
    restore_points = get_restore_points(args.url, token)

    vm_restore_points = [restore_point for restore_point in restore_points['data'] if restore_point['name'] == args.vm_name]
    if not vm_restore_points:
        print(f"CRITICAL: No restore points found for VM {args.vm_name}")
        sys.exit(2)

    latest_restore_point = max(vm_restore_points, key=lambda x: x['creationTime'])
    if latest_restore_point['malwareStatus']!= 'Clean':
        print(f"CRITICAL: Malware status for VM {args.vm_name} is not Clean")
        sys.exit(2)

    backup_id = latest_restore_point['backupId']
    backup_status = get_backup_status(args.url, token, backup_id)
    if not backup_status:
        print(f"CRITICAL: Failed to get backup status for VM {args.vm_name}")
        sys.exit(2)

    creation_time = datetime.strptime(latest_restore_point['creationTime'], '%Y-%m-%dT%H:%M:%S.%f%z')
    time_diff = datetime.now(creation_time.tzinfo) - creation_time
    if time_diff.total_seconds() / 3600 > args.max_backup_age:
        print(f"CRITICAL: Backup for VM {args.vm_name} is older than {args.max_backup_age} hours")
        sys.exit(2)

    print(f"OK: Backup for VM {args.vm_name} is successful and within the allowed age of {args.max_backup_age} hours")
    sys.exit(0)

if __name__ == '__main__':
    main()
