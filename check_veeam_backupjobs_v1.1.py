#!/usr/bin/env python3
#Veeam API Version 1.1
# ./check_veeam_backupjobs.py --url https://<VEEAM SERVER>:9419 --credentials_file <PATH> --max_backup_age <AGE> --job_filter "<OPTIONAL FILTER>"
import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)

def read_credentials(credentials_file):
    with open(credentials_file, 'r') as f:
        lines = f.readlines()
        username = lines[0].strip()
        password = lines[1].strip()
        return username, password

def get_api_key(url, username, password):
    response = requests.post(f'{url}/api/oauth2/token', headers={
        'Accept': 'application/json',
        'x-api-version': '1.1-rev2',
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'grant_type': 'password',
        'username': username,
        'password': password,
      'refresh_token': '',
        'code': '',
        'use_short_term_refresh': '',
        'vbr_token': ''
    }, verify=False)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f'Failed to authenticate with Veeam API: {response.status_code}')
        print(f'Response headers: {response.headers}')
        print(f'Response text: {response.text}')
        raise Exception(f'Failed to authenticate with Veeam API: {response.text}')

def get_jobs_states(url, api_key):
    headers = {
        'Accept': 'application/json',
        'x-api-version': '1.1-rev2',
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.get(f'{url}/api/v1/jobs/states', headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to retrieve jobs from Veeam API: {response.status_code}')
        print(f'Response headers: {response.headers}')
        print(f'Response text: {response.text}')
        raise Exception(f'Failed to retrieve jobs from Veeam API: {response.text}')

def main():
    parser = argparse.ArgumentParser(description='Check Veeam backup jobs')
    parser.add_argument('--url', help='Veeam server URL', required=True)
    parser.add_argument('--credentials_file', help='Path to credentials file', required=True)
    parser.add_argument('--max_backup_age', help='Maximum allowed backup age in hours', required=True, type=int)
    parser.add_argument('--job_filter', help='Filter jobs by name', default=None)
    args = parser.parse_args()

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
