Explanation of the Script:
Backup Details API Request:

The script makes a GET request to the /rest/appliance/recovery/backup/job/details API endpoint.
The backup details include status, start_time, and end_time (in ISO 8601 format).
Backup Status:

The script checks the status field for the backup, which should be "SUCCEEDED".
If the status is not "SUCCEEDED", it returns a CRITICAL state.
Backup Age Check:

It calculates the time difference between the current time and the end_time of the last backup.
If the backup is older than the configured AGE_THRESHOLD (in hours), it returns CRITICAL.
Success:

If everything is fine, the script returns OK with the time since the last successful backup.


command
./check_vcenter_backup.sh -h your_vcenter_host -u your_vcenter_username -p 'your_vcenter_password' -t 'AGE_THRESHOLD'
