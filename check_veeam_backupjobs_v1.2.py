#!/usr/bin/env python3
#Veeam API Version 1.2
# ./check_veeam_backupjobs.py --url https://<VEEAM SERVER>:9419 --credentials_file <PATH> --max_backup_age <AGE> --job_filter "<OPTIONAL FILTER>"
import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
import subprocess
import urllib.request
import urllib.parse

logging.basicConfig(level=logging.INFO)

def read_credentials(credentials_file):
    with open(credentials_file, 'r') as f:
        lines = f.readlines()
        username = lines[0].strip()
        password = lines[1].strip()
        return username, password

def get_api_key(url, username, password):
    response = subprocess.run([
        'curl',
        '-X',
        'POST',
        f'{url}/api/oauth2/token',
        '-H',
        'accept: application/json',
        '-H',
        'x-api-version: 1.2-rev0',
        '-H',
        'Content-Type: application/x-www-form-urlencoded',
        '-d',
        f'grant_type=password&username={username}&password={password}&refresh_token=&code=&use_short_term_refresh=&vbr_token=',
        '-k'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    token_response = json.loads(response.stdout.decode('utf-8'))
    return token_response['access_token']

def get_jobs_states(url, api_key):
    headers = {
        'accept': 'application/json',
        'x-api-version': '1.2-rev0',
        'Authorization': f'Bearer {api_key}'
    }
    req = urllib.request.Request(f'{url}/api/v1/jobs/states', headers=headers)
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

def main():
    parser = argparse.ArgumentParser(description='Check Veeam backup jobs')
    parser.add_argument('--url', help='Veeam server URL', required=True)
    parser.add_argument('--credentials_file', help='Path to credentials file', required=True)
    parser.add_argument('--max_backup_age', help='Maximum allowed backup age in hours', required=True, type=int)
    parser.add_argument('--job_filter', help='Filter jobs by name', default=None)
    args = parser.parse_args()

    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

    username, password = read_credentials(args.credentials_file)
    api_key = get_api_key(args.url, username, password)
    jobs_states = get_jobs_states(args.url, api_key)

    failed_jobs = []
    successful_jobs = 0
    warning_jobs = []
    for job in jobs_states['data']:
        job_name = job['name']
        if job['lastRun'] is not None and datetime.strptime(job['lastRun'], '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=None) > datetime.now() - timedelta(hours=args.max_backup_age):
            if args.job_filter is None or args.job_filter.lower() in job_name.lower():
                if job['lastResult'] == 'Success':
                    successful_jobs += 1
                elif job['lastResult'] == 'Warning':
                    warning_jobs.append(job)
                elif job['lastResult'] == 'Failed':
                    failed_jobs.append(job)

    if failed_jobs:
        print(f"CRITICAL: Failed jobs within the allowed age range:")
        for job in failed_jobs:
            print(f"  - {job['name']}")
        if warning_jobs:
            print(f"Warning jobs: {len(warning_jobs)}")
            for job in warning_jobs:
                print(f"  - {job['name']}")
        print(f"Successful jobs: {successful_jobs}")
        sys.exit(2)
    elif warning_jobs:
        print(f"WARNING: Warning jobs within the allowed age range:")
        for job in warning_jobs:
            print(f"  - {job['name']}")
        print(f"Successful jobs: {successful_jobs}")
        sys.exit(1)
    else:
        print(f"OK: No failed or warning jobs found within the allowed age of {args.max_backup_age} hours")
        print(f"Successful jobs: {successful_jobs}")
        sys.exit(0)

if __name__ == '__main__':
    main()
