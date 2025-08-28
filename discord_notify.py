import os
import requests
from textwrap import wrap
import time

# 1) Read from ENV, not hardcoded URL
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def notify_discord(text: str):
    """
    Send a message to Discord via webhook.
    Splits messages >2000 chars (Discord limit). Simple retry on 429/5xx.
    """
    if not DISCORD_WEBHOOK_URL:
        print("No DISCORD_WEBHOOK_URL set; skipping Discord notify.")
        return

    # Discord hard limit is 2000 chars per message
    parts = wrap(text, 1900, break_long_words=False, replace_whitespace=False) or ["(empty)"]

    for part in parts:
        for attempt in range(3):
            try:
                r = requests.post(DISCORD_WEBHOOK_URL, json={"content": part}, timeout=15)
                # Discord webhooks return 204 No Content on success
                if r.status_code == 204:
                    break
                # Handle rate limit
                if r.status_code == 429:
                    retry = float(r.headers.get("Retry-After", "1"))
                    print(f"Rate limited; sleeping {retry}s")
                    time.sleep(retry)
                    continue
                r.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == 2:
                    print(f"Discord post failed: {e}")
                else:
                    time.sleep(2 * (attempt + 1))
