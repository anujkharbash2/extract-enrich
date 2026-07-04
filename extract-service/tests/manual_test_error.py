import requests
import json

response = requests.post(
    "http://localhost:8001/v1/extract",
    json={
        "html": None,
        "statusCode": None,
        "renderTimeMs": None,
        "finalUrl": None,
        "error": "BLOCKED",
        "proxyId": "test-proxy-1",
    },
)
print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2))