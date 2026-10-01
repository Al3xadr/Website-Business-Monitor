import sys
from checker import check_site


REASON_TEXT = {
    "OK": "Site is reachable",
    "TIMEOUT": "Connection timeout",
    "CONNECTION_ERROR": "Could not connect to site",
}


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

result = check_site(url)

if result["status_code"] is not None:
    print(f"HTTP status: {result['status_code']}")

if result["response_time"] is not None:
    print(f"Response time: {result['response_time']:.2f} seconds")

if result["reason"] and result["reason"] not in REASON_TEXT:
    # HTTP_404 и подобные
    print(f"Reason: {result['reason']}")
elif result["reason"]:
    print(f"Reason: {REASON_TEXT[result['reason']]}")

print()
print(f"Status: {'UP' if result['ok'] else 'DOWN'}")