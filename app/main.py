import sys
import requests
import time 



url = sys.argv[1]


print("================================")
print("       SITE MONITOR")
print("================================")
print()
print(f"URL: {url}")
print()

try:
    start = time.time()
    response = requests.get(url, timeout=5)
    print(f"HTTP status: {response.status_code}")
    end = time.time()
    elapsed = end - start
    print(f"Response time: {elapsed:.2f} seconds")

    if response.status_code == 200:
        print("Status: UP")
    else:
        print("Status: DOWN")

except Exception as e:
    print("HTTP status: —")
    print("Status: DOWN")
    print(f"Error: {e}")