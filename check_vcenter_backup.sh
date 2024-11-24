#!/bin/bash

# Nagios Plugin to check vCenter backup status

# Default values (these can be overridden by command-line arguments)
VCENTER_HOST="your_vcenter_host"
VCENTER_USER="your_vcenter_username"
VCENTER_PASS="your_vcenter_password"
AGE_THRESHOLD=25 # default threshold for backup age in hours
VCENTER_API="/rest/appliance/recovery/backup/job/details"

# Usage function to display help message
usage() {
  echo "Usage: $0 -h <vcenter_host> -u <vcenter_user> -p <vcenter_password> -t <age_threshold_in_hours>"
  echo "  -t : Age threshold in hours for the backup (default is 25 hours)"
  exit 3
}

# Parse command-line arguments
while getopts "h:u:p:t:" opt; do
  case "$opt" in
    h) VCENTER_HOST="$OPTARG" ;;
    u) VCENTER_USER="$OPTARG" ;;
    p) VCENTER_PASS="$OPTARG" ;;
    t) AGE_THRESHOLD="$OPTARG" ;;
    *) usage ;;
  esac
done

# Check if all necessary arguments are provided
if [[ -z "$VCENTER_HOST" || -z "$VCENTER_USER" || -z "$VCENTER_PASS" ]]; then
  echo "CRITICAL: Missing required arguments"
  usage
fi

# Get the current timestamp
CURRENT_TIMESTAMP=$(date +%s)

# Function to get backup job details
get_backup_details() {
  curl -s -k -u "${VCENTER_USER}:${VCENTER_PASS}" -X GET "https://${VCENTER_HOST}${VCENTER_API}"
}

# Get backup job details
BACKUP_DETAILS=$(get_backup_details)

# Extract the backup status, start time, and end time using jq
BACKUP_STATUS=$(echo "$BACKUP_DETAILS" | jq -r '.value[0].value.status')
START_TIME=$(echo "$BACKUP_DETAILS" | jq -r '.value[0].value.start_time')
END_TIME=$(echo "$BACKUP_DETAILS" | jq -r '.value[0].value.end_time')

# Check if we got valid values
if [[ -z "$BACKUP_STATUS" || "$BACKUP_STATUS" == "null" ]]; then
  echo "CRITICAL: Could not retrieve backup status"
  exit 2
fi

if [[ "$BACKUP_STATUS" != "SUCCEEDED" ]]; then
  echo "CRITICAL: Last backup failed or is incomplete"
  exit 2
fi

# Convert the backup end time to seconds since epoch
BACKUP_END_TIMESTAMP_SEC=$(date -d "${END_TIME}" +%s)

# Calculate the time since the last backup in hours
TIME_DIFF=$(( (CURRENT_TIMESTAMP - BACKUP_END_TIMESTAMP_SEC) / 3600 ))

# Check backup age against threshold
if [[ ${TIME_DIFF} -ge ${AGE_THRESHOLD} ]]; then
  echo "CRITICAL: Last backup was ${TIME_DIFF} hours ago, exceeding threshold of ${AGE_THRESHOLD} hours"
  exit 2
else
  echo "OK: Last backup was ${TIME_DIFF} hours ago"
  exit 0
fi
