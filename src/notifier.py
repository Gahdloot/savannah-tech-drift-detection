import requests
import json

def send_teams_alert(diff, webhook_url):
    if not diff:
        return "No drift detected."
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Configuration Drift Detected",
        "text": f"Drift Summary:\n```json\n{json.dumps(diff, indent=2)}```"
    }
    response = requests.post(webhook_url, json=message)
    return response.status_code