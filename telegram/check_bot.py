"""Read-only Telegram bot identity check (never exposes the token)."""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED_USERNAME = "IlBotScomodo_bot"


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("CONFIG_REQUIRED: Add TELEGRAM_BOT_TOKEN as a GitHub Actions repository secret.")
        return 2
    # An accidental traceback or full URL would disclose the bearer credential:
    # handle all network/API errors without printing request URLs.
    print("::add-mask::" + token)
    request = Request(
        "https://api.telegram.org/bot" + token + "/getMe",
        headers={"Accept": "application/json", "User-Agent": "AKE-Telegram-Bot-Check/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read(100_000))
    except HTTPError as error:
        print("Telegram API returned HTTP " + str(error.code) + " (no secrets logged).")
        return 3
    except (URLError, ValueError, OSError):
        print("Telegram connectivity or response format failure (no secrets logged).")
        return 4

    identity = payload.get("result", {}) if isinstance(payload, dict) else {}
    username = identity.get("username", "") if isinstance(identity, dict) else ""
    if not payload.get("ok") or not identity.get("is_bot") or username.lower() != EXPECTED_USERNAME.lower():
        print("BOT_MISMATCH: The configured token belongs to a different bot, or Telegram did not confirm its identity.")
        return 5

    print("CONNECTED: @" + username + " verified successfully.")
    print("This is an identity check only: no inbox polling, no outgoing messages and no public webhook.")
    print("Next: owner-only authorization before receiving commands or sending alerts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
