import argparse
import requests
import json

# Replace with your production Slack Webhook URL
DEFAULT_WEBHOOK = ""

def send_slack_card(status, build_num, action, error_details, webhook):
    if not webhook or not webhook.strip():
        print("Slack Webhook URL is not configured. Skipping notification.")
        return

    # Color coding depending on pipeline execution status
    if status.upper() == "SUCCESS":
        color = "#2eb886"  # Green
        title = f"🟢 Deployment Successful - Build #{build_num}"
        text = "The pipeline build and tests completed successfully. Deployment is healthy."
    elif status.upper() == "FAILED":
        color = "#a30200"  # Red
        title = f"🔴 Pipeline Failure - Build #{build_num}"
        text = f"An error occurred during build/deploy verification. Details: *{error_details}*"
    elif status.upper() == "HEALED":
        color = "#2eb886"  # Green
        title = f"✅ Self-Healing Successful - Build #{build_num}"
        text = f"The pipeline recovered successfully! Action taken: *{action}*."
    elif status.upper() == "ROLLBACK":
        color = "#e8a200"  # Amber
        title = f"⚠️ Auto-Rollback Executed - Build #{build_num}"
        text = f"Deployment verified unhealthy. Automatically rolled back Helm release to last stable version."
    else:
        color = "#707070"  # Grey
        title = f"ℹ️ Pipeline Status Update - Build #{build_num}"
        text = f"Pipeline execution reached status: *{status}*."

    payload = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": text,
                "fields": [
                    {
                        "title": "Pipeline Action",
                        "value": action if action else "None Required",
                        "short": True
                    },
                    {
                        "title": "Build Number",
                        "value": f"#{build_num}",
                        "short": True
                    }
                ],
                "footer": "Self-Healing DevSecOps Pipeline Notifier",
                "ts": None
            }
        ]
    }

    try:
        response = requests.post(webhook, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, timeout=10)
        if response.status_code == 200:
            print("Successfully sent Slack alert.")
        else:
            print(f"Failed to send Slack alert. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending Slack alert: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--status', required=True)
    parser.add_argument('--build', required=True)
    parser.add_argument('--action', default="")
    parser.add_argument('--error', default="")
    parser.add_argument('--webhook', default=DEFAULT_WEBHOOK)
    args = parser.parse_args()
    send_slack_card(args.status, args.build, args.action, args.error, args.webhook)
