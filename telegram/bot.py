"""Owner-restricted, read-only Telegram control plane for Il Bot Scomodo.

Runs as a short GitHub Actions job and consumes updates in batches.
No webhook, no server, no wallet operations, no shell commands from Telegram.
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = "ilbotscomodo/superteam-earn-agent"
BOT_USERNAME = "IlBotScomodo_bot"
MAX_UPDATES = 25


class RemoteError(Exception):
    pass


def request_json(url: str, *, payload=None, bearer: str | None = None):
    headers = {
        "User-Agent": "IlBotScomodo-Control/1.0",
        "Accept": "application/json",
    }
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urlopen(request, timeout=25) as response:
            raw = response.read(1_000_000)
            return json.loads(raw.decode("utf-8"))
    except HTTPError as err:
        # The Telegram token appears in the URL. NEVER print a full exception or URL.
        raise RemoteError("Remote HTTP " + str(err.code)) from None
    except (URLError, UnicodeError, ValueError, OSError):
        raise RemoteError("Remote connection or response failure") from None


def telegram(token: str, method: str, params: dict):
    data = request_json("https://api.telegram.org/bot" + token + "/" + method, payload=params)
    if not isinstance(data, dict) or not data.get("ok"):
        raise RemoteError("Telegram API rejected the request")
    return data.get("result")


def github(path: str, token: str):
    if not token:
        raise RemoteError("GitHub Actions read token not configured")
    return request_json("https://api.github.com/repos/" + REPO + path, bearer=token)


def status_text(gh_token: str):
    try:
        data = github("/actions/runs?per_page=20", gh_token)
        runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
        scout = next((r for r in runs if r.get("name") ==
                       "Superteam agent-eligible opportunity scout"), None)
        if scout:
            state = scout.get("conclusion") or scout.get("status") or "unknown"
            scanned = str(scout.get("created_at") or "?").replace("T", " ")[:16] + " UTC"
            scout_line = "Scout: " + state + " (ultima esecuzione: " + scanned + ")"
        else:
            scout_line = "Scout: nessuna esecuzione recente trovata"
        data = github("/issues?state=open&per_page=100", gh_token)
        opportunities = sum(1 for item in data if isinstance(item, dict) and
                            "<!-- superteam-scout-id:" in str(item.get("body", "")))
        return ("🤖 Il Bot Scomodo — STATO\n"
                "Telegram: operativo (lettura e risposte)\n"
                + scout_line + "\n"
                + "Bounty individuate e aperte su GitHub: " + str(opportunities) + "\n"
                "Candidature/vittorie/incassi: non confermati.\n"
                "Controlla i dettagli su https://github.com/" + REPO + "/issues")
    except RemoteError:
        return "GitHub non raggiungibile al momento. Il bot Telegram e' comunque operativo."


def opportunities_text(gh_token: str):
    try:
        rows = github("/issues?state=open&per_page=50", gh_token)
        if not isinstance(rows, list):
            return "Impossibile leggere le opportunita' in questo momento."
        items = [r for r in rows if isinstance(r, dict) and
                 "<!-- superteam-scout-id:" in str(r.get("body", ""))]
        if not items:
            return "Nessuna bounty ancora registrata come issue aperta."
        lines = ["🔎 Ultime opportunita' da valutare (NON vinte):"]
        for row in items[:5]:
            title = re.sub(r"[\r\n\t]+", " ", str(row.get("title", "")))[:125]
            issue_number = int(row.get("number", 0))
            lines.append("• " + title + "\nhttps://github.com/" + REPO + "/issues/" + str(issue_number))
        return "\n".join(lines)
    except (RemoteError, ValueError, TypeError):
        return "GitHub non raggiungibile al momento. Riprova piu' tardi."


def reply_for(message: dict, owner_id: str, gh_token: str):
    """Return a text reply or None. Only private chats can issue commands."""
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    if chat.get("type") != "private" or sender.get("is_bot"):
        return None
    sender_id = sender.get("id")
    chat_id = chat.get("id")
    if not isinstance(sender_id, int) or chat_id != sender_id:
        return None
    body = str(message.get("text") or "").strip()
    if not body.startswith("/"):
        return None
    command = body.split(maxsplit=1)[0].lower().split("@", 1)
    if len(command) > 1 and command[1] != BOT_USERNAME.lower():
        return None
    name = command[0]
    if name in ("/id", "/start"):
        return ("🤖 Ciao! Il tuo Telegram User ID e': " + str(sender_id)
                + "\nPer attivare i comandi riservati, salva questo numero come secret"
                " TELEGRAM_OWNER_ID nel repository GitHub del progetto."
                "\nNon inviare mai il token del bot.")
    if not owner_id or str(sender_id) != owner_id:
        return "🔒 Comando riservato. Scrivi /id per conoscere il tuo User ID."
    if name in ("/help", "/aiuto"):
        return ("🤖 Comandi disponibili:\n"
                "/id - mostra il tuo User ID\n"
                "/status - stato monitoraggio AKE\n"
                "/opportunita - ultime bounty trovate\n"
                "/help - questo menu\n\n"
                "Il bot non accetta ordini di spesa, trasferimenti crypto o codice eseguibile.")
    if name == "/status":
        return status_text(gh_token)
    if name in ("/opportunita", "/opportunities"):
        return opportunities_text(gh_token)
    return "Comando non riconosciuto. Scrivi /help."


def process_once(token: str, owner_id: str, gh_token: str) -> int:
    updates = telegram(token, "getUpdates", {
        "timeout": 0, "limit": MAX_UPDATES,
        "allowed_updates": ["message"],
    })
    if not isinstance(updates, list):
        raise RemoteError("Telegram returned an invalid updates list")
    last_id = None
    replies = 0
    for row in updates:
        if not isinstance(row, dict) or not isinstance(row.get("update_id"), int):
            continue
        message = row.get("message")
        if isinstance(message, dict):
            answer = reply_for(message, owner_id, gh_token)
            if answer:
                telegram(token, "sendMessage", {
                    "chat_id": message["chat"]["id"],
                    "text": answer[:3900],
                    "disable_web_page_preview": True,
                })
                replies += 1
        last_id = row["update_id"]
    # Confirm updates only after replies have been sent.
    if last_id is not None:
        telegram(token, "getUpdates", {
            "offset": last_id + 1,
            "timeout": 0, "limit": 1,
            "allowed_updates": ["message"],
        })
    return replies


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    owner_id = os.environ.get("TELEGRAM_OWNER_ID", "").strip()
    gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo != REPO:
        print("Wrong repository for this bot.")
        return 2
    if not token:
        print("Missing TELEGRAM_BOT_TOKEN secret.")
        return 2
    if owner_id and (not owner_id.isdecimal() or len(owner_id) > 20):
        print("TELEGRAM_OWNER_ID must be a numeric Telegram user ID.")
        return 2
    print("::add-mask::" + token)
    try:
        n = process_once(token, owner_id, gh_token)
    except RemoteError as error:
        print("Telegram bot polling failed: " + str(error))
        return 1
    print("Processed a batch; replies delivered: " + str(n))
    if not owner_id:
        print("SETUP: Awaiting TELEGRAM_OWNER_ID secret. Only /start and /id respond.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
