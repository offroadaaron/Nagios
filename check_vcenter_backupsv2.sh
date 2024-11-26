#!/bin/bash

# Default values for server, port, username, and password
server="vcenter.example.com"
port="5480"
username="your_username"
password="your_password"

# Parse command-line arguments for server, port, username, and password
while getopts "s:p:u:P:" opt; do
  case "$opt" in
    s) server="$OPTARG" ;;  # Set the server URL
    p) port="$OPTARG" ;;    # Set the port number
    u) username="$OPTARG" ;;# Set the username
    P) password="$OPTARG" ;;# Set the password
    ?) echo "Usage: $0 [-s server] [-p port] [-u username] [-P password]"
       exit 2 ;;
  esac
done

# API URL for backup job details
api_url="https://$server:$port/rest/appliance/recovery/backup/job/details"

# Fetch the backup job details in JSON format using curl
response=$(curl -s -k -u "$username:$password" "$api_url")

# Ensure the response is not empty
if [ -z "$response" ]; then
    echo "CRITICAL: Failed to fetch backup details."
    exit 2
fi

# Initialize counters
successful_backups=0
failed_backups=0

# Extract timestamp and location of the last backup
last_backup_timestamp=$(echo "$response" | jq -r '.value[0].value.start_time')
last_backup_location=$(echo "$response" | jq -r '.value[0].value.location')

# Loop through the backup jobs to count successes and failures
total_backups=$(echo "$response" | jq -r '.value | length')
for i in $(seq 0 $((total_backups - 1))); do
    status=$(echo "$response" | jq -r ".value[$i].value.status")
    if [ "$status" == "SUCCEEDED" ]; then
        successful_backups=$((successful_backups + 1))
    else
        failed_backups=$((failed_backups + 1))
    fi
done

# Prepare the output message
echo "Last backup timestamp: $last_backup_timestamp"
echo "Backup location: $last_backup_location"

if [ "$failed_backups" -eq 0 ]; then
    echo "OK: All $successful_backups backups were successful."
    exit 0
else
    echo "WARNING: $successful_backups successful backups, $failed_backups failed backups."
    exit 1
fi
