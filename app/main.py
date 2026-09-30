import sys
import requests
import time


url = sys.argv[1]


print("================================")
print("       Website Business Monitor")
print("================================")
print()
print(f"URL: {url}")
print()

try:
    start = time.time()

    response = requests.get(url, timeout=5)

    end = time.time()

    elapsed = end - start

    print(f"HTTP status: {response.status_code}")
    print(f"Response time: {elapsed:.2f} seconds")

    if 200 <= response.status_code <= 399:
        print("Status: UP")
    else:
        print("Status: DOWN")

except requests.exceptions.RequestException as e:
    print("HTTP status: —")
    print("Status: DOWN")
    print("Error: Could not connect to site")