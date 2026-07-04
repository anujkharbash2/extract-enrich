import requests
import json

with open("tests/fixtures/sample_article.html", "r", encoding="utf-8") as f:
    html = f.read()

response = requests.post(
    "http://localhost:8001/v1/extract",
    json={
        "html": html,
        "statusCode": 200,
        "renderTimeMs": 1200,
        "finalUrl": "https://www.thehindu.com/news/international/west-asia-war-live-updates-july-3-2026-iran-israel-usa-strait-of-hormuz/article71177098.ece",
        "error": None,
        "proxyId": "test-proxy-1",
    },
)
print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2))