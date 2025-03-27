#!/bin/bash
#./check_trend_connectivity.sh <API KEY> <ENDPOINT NAME>

# Define the API URL
API_URL="https://api.au.xdr.trendmicro.com/v3.0/endpointSecurity/endpoints"

# Check if the API key file and endpoint name were provided as command-line arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <API_KEY_FILE> <ENDPOINT_NAME>"
  exit 3
fi

# Set the API key file and endpoint name from the command-line arguments
API_KEY_FILE="$1"
ENDPOINT_NAME="$2"

# Read the API key from the file
API_KEY=$(cat "$API_KEY_FILE")

# Run the curl command and store the output in a variable
OUTPUT=$(curl -s -X GET "$API_URL?select=endpointName%2CedrSensorConnectivity%2CeppAgentLastConnectedDateTime" -H "TMV1-Filter: endpointName eq \"$ENDPOINT_NAME\"" -H "Authorization: Bearer $API_KEY")

# Parse the output to get the connectivity status
CONNECTIVITY=$(echo "$OUTPUT" | jq -r '.items[0].edrSensor.connectivity')

# Check if the output is not empty
if [ -z "$CONNECTIVITY" ]; then
  echo "Error: Unable to retrieve connectivity status"
  exit 3
fi

# Check if the endpoint is connected
if [ "$CONNECTIVITY" = "connected" ]; then
  echo "Trend Vision One Endpoint $ENDPOINT_NAME is connected."
  exit 0
else
  echo "Trend Vision One Endpoint $ENDPOINT_NAME is disconnected."
  exit 2
fi
