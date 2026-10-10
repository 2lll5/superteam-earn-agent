"""Find agent-eligible Superteam opportunities and optionally file GitHub issues.

Never creates Superteam submissions, never calls wallet APIs, and never spends funds.
Only requests the documented authenticated live-listings endpoint.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

EARN_BASE = "https://superteam.fun"
GH_BASE = "https://api.github.com"
AGENT_ELIGIBLE = {"AGENT_ALLOWED", "AGENT_ONLY"}
KEYWORDS = {
    "python": 5, "research": 5, "data analysis": 5, "analytics": 4,
    "documentation": 4, "technical writing": 4, "api": 3,
    "video": 3, "social media": 3, "content": 2, "automation": 5,
    "script": 4, "bug": 3, "testing": 3, "audit": 4,
    "developer tool": 3, "web3": 1, "ai agent": 3,
}
EXPENSIVE_OR_UNSAFE = (
    "upfront payment", "buy tokens", "purchase a token", "deposit to enter",
    "stake funds", "pay to enter", "entry fee", "private key",
)
SPECIALIZED = ("anchor program", "move smart contract", "solidity audit")


def request_json(url: str, token: str | None = None, body=None, method: str | None = None):
    headers = {"Accept": "application/json", "User-Agent": "ilbotscomodo-superteam-scout/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method or ("POST" if data else "GET"))
    try:
        with urlopen(req, timeout=25) as r:
            raw = r.read(3_000_000)
            return json.loads(raw.decode("utf-8")), dict(r.headers)
    except HTTPError as e:
        # Do not print request headers or API keys.
        raise RuntimeError(f"HTTP {e.code} from {url.split('?')[0]}") from None
    except URLError as e:
        raise RuntimeError("Network error while contacting the service") from e


def unwrap_listings(payload):
    """Recognize supported response envelopes; fail safely on unfamiliar APIs."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("listings", "items", "results", "opportunities", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = unwrap_listings(value)
                if nested is not None:
                    return nested
    return None


def get_value(row, *keys):
    for key in keys:
        v = row.get(key)
        if v not in (None, ""):
            return v
    return None


def listing_summary(row: dict):
    title = str(get_value(row, "title", "name") or "Untitled listing").strip()
    slug = str(get_value(row, "slug", "listingSlug") or "").strip()
    lid = str(get_value(row, "id", "listingId", "_id") or slug).strip()
    if not lid:
        raise ValueError("Listing without an ID or slug")
    access = str(get_value(row, "agentAccess", "agent_access") or "").upper()
    # The agent-listings endpoint itself is the eligibility filter.
    # If it explicitly declares a human-only item, reject it.
    if access and access not in AGENT_ELIGIBLE:
        return None
    synopsis = " ".join(str(row.get(k, "")) for k in (
        "title", "description", "shortDescription", "type", "skills", "tags"
    )).lower()
    if any(x in synopsis for x in EXPENSIVE_OR_UNSAFE):
        return None
    points = sum(value for keyword, value in KEYWORDS.items() if keyword in synopsis)
    if any(x in synopsis for x in SPECIALIZED):
        points -= 6
    date = str(get_value(row, "deadline", "deadlineAt", "endsAt", "endDate") or "")
    compensation = get_value(row, "reward", "rewards", "prize", "compensation", "totalReward", "usdValue")
    link = str(get_value(row, "url", "link") or (f"{EARN_BASE}/earn/listing/{quote(slug)}" if slug else ""))
    if link and not link.startswith("https://superteam.fun/"):
        # Link is provided as a neutral reference, never executed.
        link = link.replace("\n", " ")
    return {"id": lid, "slug": slug, "title": title[:200], "access": access or "AGENT_API_FEED",
            "score": points, "deadline": date, "reward_raw": compensation, "link": link,
            "type": str(get_value(row, "type", "listingType") or "")}


def issue_identity(item):
    return f"<!-- superteam-scout-id:{item['id']} -->"


def issue_body(item):
    reward = json.dumps(item["reward_raw"], ensure_ascii=False, default=str)
    return (f"{issue_identity(item)}\n\n"
            "**Automatically discovered; not a submitted application.**\n\n"
            f"- Listing: {item['link'] or 'URL unavailable — inspect on Superteam'}\n"
            f"- Agent eligibility: `{item['access']}` (per official agent API)\n"
            f"- Kind: {item['type'] or 'unknown'}\n"
            f"- Deadline (raw): {item['deadline'] or 'not provided'}\n"
            f"- Compensation (raw, unverified): `{reward[:1000]}`\n"
            f"- Skill score: {item['score']} (heuristic, NOT a payout prediction)\n\n"
            "**Before doing work:** open the details, confirm eligibility, scope, currency,"
            " acceptance criteria, due date, and whether AI-generated work is allowed. "
            "Do not prepay, connect wallets, sign transactions, or disclose secrets.\n\n"
            "Status: NOT STARTED / NOT SUBMITTED / NOT WON.\n")


def existing_issue_ids(repo, gh_token):
    found = set()
    for page in range(1, 6):
        url = f"{GH_BASE}/repos/{quote(repo, safe='/')}/issues?state=all&per_page=100&page={page}"
        rows, _ = request_json(url, token=gh_token)
        if not isinstance(rows, list):
            raise RuntimeError("Unexpected GitHub issues API response")
        for issue in rows:
            if "pull_request" in issue:
                continue
            match = re.search(r"<!-- superteam-scout-id:(.*?) -->", str(issue.get("body") or ""))
            if match:
                found.add(match.group(1))
        if len(rows) < 100:
            break
    return found


def write_summary(items, total):
    lines = ["## Superteam Scout", "", f"Timestamp UTC: {datetime.now(timezone.utc).isoformat()}",
             f"Agent-eligible entries examined: {total}", f"Candidates above threshold: {len(items)}", ""]
    for item in items[:20]:
        lines.append(f"- **{item['title']}** — score {item['score']} — {item['link']}")
    text = "\n".join(lines)+"\n"
    print(text)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as out:
            out.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--create-issues", action="store_true", help="File at most 3 new GitHub issues per scan")
    ap.add_argument("--min-score", type=int, default=4)
    a = ap.parse_args(argv)
    key = os.environ.get("SUPERTEAM_API_KEY", "").strip()
    if not key:
        print("Missing SUPERTEAM_API_KEY GitHub Actions secret", file=sys.stderr)
        return 2
    payload, _ = request_json(f"{EARN_BASE}/api/agents/listings/live?take=20", token=key)
    rows = unwrap_listings(payload)
    if rows is None:
        print("Unknown Superteam API response schema: cannot safely triage", file=sys.stderr)
        return 3
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            item = listing_summary(row)
        except ValueError:
            continue
        if item and item["score"] >= a.min_score:
            items.append(item)
    items.sort(key=lambda x: (-x["score"], x["title"].lower()))
    write_summary(items, len(rows))
    if a.create_issues:
        gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
        gh_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if not gh_token or not gh_repo:
            print("Missing GITHUB_TOKEN or GITHUB_REPOSITORY", file=sys.stderr)
            return 4
        existing = existing_issue_ids(gh_repo, gh_token)
        count = 0
        for item in items:
            if item["id"] in existing:
                continue
            body = {"title": "Superteam: "+item["title"][:220], "body": issue_body(item)}
            request_json(f"{GH_BASE}/repos/{quote(gh_repo,safe='/')}/issues",
                         token=gh_token, body=body)
            print("Created issue for: "+item["title"])
            existing.add(item["id"])
            count += 1
            if count >= 3:
                break
        print(f"New issues: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
