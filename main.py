import os
from glob import glob
from src.compare import compare_snapshots
from src.notifier import send_teams_alert
from config import settings

webhook_url = "https://outlook.office.com/webhook/your-webhook-url"  # Replace with your Teams webhook

if __name__ == "__main__":
    files = sorted(glob(f"{settings.SNAPSHOT_DIR}users_*.json"))
    if len(files) < 2:
        print("Not enough snapshots to compare.")
    else:
        latest = files[-1]
        previous = files[-2]
        diff = compare_snapshots(previous, latest)
        print("Drift:", diff)
        send_teams_alert(diff, webhook_url)