import sys
import requests

url = sys.argv[1]

print("================================")
print("       SITE MONITOR")
print("================================")
print()
print(f"URL: {url}")
print()

try:
    response = requests.get(url, timeout=5)
    print(f"HTTP status: {response.status_code}")

    if response.status_code == 200:
        print("Status: UP")
    else:
        print("Status: DOWN")

except Exception as e:
    print("HTTP status: —")
    print("Status: DOWN")
    print(f"Error: {e}")