import sys
import requests
import time


if len(sys.argv) < 2:
    print("Usage: python app/main.py <URL>")
    sys.exit(1)

url = sys.argv[1]


print("======================")
print("     Website Business Monitor")
print("======================")
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
    print()

    if 200 <= response.status_code <= 399:
        print("Status: UP")
    else:
        print("Status: DOWN")

except requests.exceptions.Timeout:
    print("ERROR: Connection timeout")
    print()
    print("Status: DOWN")

except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to site")
    print()
    print("Status: DOWN")