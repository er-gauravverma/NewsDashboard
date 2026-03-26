import requests

response = requests.post(
    "https://ntfy.sh/gv_ethusdt_bot_55555",
    data="🚨 Test alert with sound!".encode('utf-8'),
    headers={
        "Title": "Python Script Alert",
        "Priority": "high",
        "Tags": "loudspeaker"
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")