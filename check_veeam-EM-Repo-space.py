#Create credentials file to look like below:
#<domain>\<username>
#<Password>
#python3 check_veeam-EM-Repo-space.py https://<veeam-server>:9398 <veeam Credentials file location> '<Repo name' 80 90
#80 = Warning; 90 = Critical - Obviously change this as needed
import http.client
import ssl
import sys
import json
from xml.etree import ElementTree as ET
import base64

# Nagios return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

def read_credentials(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) < 2:
                print(f"UNKNOWN: Password file '{file_path}' does not contain enough lines.")
                sys.exit(UNKNOWN)
            username = lines[0].strip()
            password = lines[1].strip()
            return username, password
    except Exception as e:
        print(f"UNKNOWN: Failed to read password file '{file_path}': {e}")
        sys.exit(UNKNOWN)

def get_session(url, username, password):
    host, port = url.split('//')[1].split(':')
    port = int(port)
    context = ssl._create_unverified_context()  # Disable SSL verification
    conn = http.client.HTTPSConnection(host, port, context=context)

    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_base64}'
    }

    try:
        conn.request("POST", "/api/sessionMngr/?v=latest", headers=headers)
        response = conn.getresponse()
        response_body = response.read().decode('utf-8')
#        print(f"DEBUG: Authentication response status: {response.status}")
#        print(f"DEBUG: Authentication response headers: {response.getheaders()}")
#        print(f"DEBUG: Authentication response body: {response_body}")

        if response.status == 201:
            session_id = response.getheader('X-RestSvcSessionId')
            if not session_id:
                print(f"CRITICAL: Failed to obtain session ID from response headers. Response: {response_body}")
                sys.exit(CRITICAL)
            return session_id
        elif response.status != 200:
            print(f"CRITICAL: Failed to authenticate with Veeam API: {response.status} {response.reason}. Response: {response_body}")
            sys.exit(CRITICAL)
        else:
            session_id = response.getheader('X-RestSvcSessionId')
            if not session_id:
                print(f"CRITICAL: Failed to obtain session ID from response headers. Response: {response_body}")
                sys.exit(CRITICAL)
            return session_id
    except Exception as e:
        print(f"CRITICAL: Failed to authenticate with Veeam API: {e}")
        sys.exit(CRITICAL)
    finally:
        conn.close()

def get_repository_space(url, session_id):
    host, port = url.split('//')[1].split(':')
    port = int(port)
    context = ssl._create_unverified_context()  # Disable SSL verification
    conn = http.client.HTTPSConnection(host, port, context=context)

    headers = {
        'Content-Type': 'application/json',
        'X-RestSvcSessionId': session_id
    }

    try:
        conn.request("GET", "/api/reports/summary/repository", headers=headers)
        response = conn.getresponse()
        response_body = response.read().decode('utf-8')
#        print(f"DEBUG: Repository space response status: {response.status}")
#        print(f"DEBUG: Repository space response headers: {response.getheaders()}")
#        print(f"DEBUG: Repository space response body: {response_body}")

        if response.status != 200:
            print(f"CRITICAL: Failed to retrieve repository space: {response.status} {response.reason}. Response: {response_body}")
            sys.exit(CRITICAL)
        return response_body
    except Exception as e:
        print(f"CRITICAL: Failed to retrieve repository space: {e}")
        sys.exit(CRITICAL)
    finally:
        conn.close()

def bytes_to_gb(bytes_value):
    return bytes_value / (1024 ** 3)

def parse_repository_space(data, repository_name):
    try:
        # Try to parse as JSON first
        json_data = json.loads(data)
        # Check if the JSON data contains the expected structure
        if 'Periods' in json_data:
            for period in json_data['Periods']:
                name = period.get('Name')
                if name == repository_name:
                    capacity = period.get('Capacity')
                    free_space = period.get('FreeSpace')
                    used_space = capacity - free_space
                    used_percentage = (used_space / capacity) * 100
                    return name, capacity, free_space, used_space, used_percentage
        print(f"UNKNOWN: Repository '{repository_name}' not found in JSON response.")
        sys.exit(UNKNOWN)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to parse as XML
        try:
            root = ET.fromstring(data)
            namespace = {'ns': 'http://www.veeam.com/ent/v1.0'}

            for period in root.findall('ns:Period', namespace):
                name = period.find('ns:Name', namespace).text
                if name == repository_name:
                    capacity = int(period.find('ns:Capacity', namespace).text)
                    free_space = int(period.find('ns:FreeSpace', namespace).text)
                    used_space = capacity - free_space
                    used_percentage = (used_space / capacity) * 100
                    return name, capacity, free_space, used_space, used_percentage

            print(f"UNKNOWN: Repository '{repository_name}' not found in XML response.")
            sys.exit(UNKNOWN)
        except ET.ParseError as e:
            print(f"CRITICAL: Failed to parse XML data: {e}")
 #           print(f"DEBUG: XML data: {data}")
            sys.exit(CRITICAL)

def check_repository_space(url, credentials_file, repository_name, warning_threshold, critical_threshold):
    username, password = read_credentials(credentials_file)
    session_id = get_session(url, username, password)
    data = get_repository_space(url, session_id)
    name, capacity, free_space, used_space, used_percentage = parse_repository_space(data, repository_name)

    capacity_gb = bytes_to_gb(capacity)
    free_space_gb = bytes_to_gb(free_space)
    used_space_gb = bytes_to_gb(used_space)

    message = (f"Repository: {name} | "
               f"Capacity: {capacity_gb:.2f} GB, "
               f"Free Space: {free_space_gb:.2f} GB, "
               f"Used Space: {used_space_gb:.2f} GB, "
               f"Used Percentage: {used_percentage:.2f}%")

    if used_percentage >= critical_threshold:
        print(f"CRITICAL: {message}")
        sys.exit(CRITICAL)
    elif used_percentage >= warning_threshold:
        print(f"WARNING: {message}")
        sys.exit(WARNING)
    else:
        print(f"OK: {message}")
        sys.exit(OK)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python check_repo5.py <url> <credentials_file> <repository_name> <warning_threshold> <critical_threshold>")
        sys.exit(UNKNOWN)

    url = sys.argv[1]
    credentials_file = sys.argv[2]
    repository_name = sys.argv[3]
    warning_threshold = float(sys.argv[4])
    critical_threshold = float(sys.argv[5])

    check_repository_space(url, credentials_file, repository_name, warning_threshold, critical_threshold)
