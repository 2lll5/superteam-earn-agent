#!/usr/bin/env python3
"""One-time Superteam agent registration from GitHub Actions.

The only persistent credentials are GitHub Actions encrypted repository secrets.
Never emits the API key or claim code as a log, issue, artifact, or source file.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from nacl.public import PublicKey, SealedBox

GITHUB_API = "https://api.github.com"
SUPERTEAM_URL = "https://superteam.fun/api/agents"
SECRETS = ("SUPERTEAM_API_KEY", "SUPERTEAM_CLAIM_CODE")


class BootstrapError(Exception):
    pass


def github(path: str, pat: str, method: str = "GET", payload=None, missing_ok=False):
    headers = {
        "Authorization": "Bearer " + pat,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "IlBotScomodo-Scout-Bootstrap",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(GITHUB_API + path, headers=headers, data=data, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read(1_000_000)
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        if missing_ok and exc.code == 404:
            return None
        raise BootstrapError(f"GitHub API returned HTTP {exc.code} for {method} {path}") from None
    except URLError:
        raise BootstrapError("Network error contacting GitHub") from None


def register_agent():
    body = json.dumps({"name": "Il Bot Scomodo Scout"}).encode("utf-8")
    req = Request(
        SUPERTEAM_URL,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "IlBotScomodo-Scout-Bootstrap"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=40) as response:
            payload = json.loads(response.read(100_000))
    except HTTPError as exc:
        raise BootstrapError(f"Superteam registration returned HTTP {exc.code}") from None
    except URLError:
        raise BootstrapError("Network error contacting Superteam") from None

    if isinstance(payload, dict):
        # Official docs show a flat object; accept a single data wrapper as well.
        item = payload.get("data", payload)
    else:
        item = None
    if not isinstance(item, dict):
        raise BootstrapError("Unexpected Superteam registration response format")
    key = item.get("apiKey")
    claim = item.get("claimCode")
    if not (isinstance(key, str) and key.startswith("sk_") and
            isinstance(claim, str) and claim.strip()):
        raise BootstrapError("Superteam response lacks an API key or claim code")
    # Mask in GitHub logs as an extra safeguard. We never print plaintext.
    print("::add-mask::" + key)
    print("::add-mask::" + claim)
    return key, claim, str(item.get("agentId", "")), str(item.get("username", ""))


def encrypt_for_github(secret_value: str, key_base64: str) -> str:
    public_key = PublicKey(base64.b64decode(key_base64, validate=True))
    return base64.b64encode(SealedBox(public_key).encrypt(secret_value.encode("utf-8"))).decode("ascii")


def main():
    pat = os.environ.get("GH_BOOTSTRAP_PAT", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not pat:
        raise BootstrapError("Missing GH_BOOTSTRAP_PAT. Add it as a GitHub Actions repository secret.")
    if repo != "ilbotscomodo/superteam-earn-agent":
        raise BootstrapError("Repository does not match the approved target.")

    api_path = f"/repos/{repo}/actions/secrets"
    # Preflight ALL required GitHub endpoints BEFORE contacting Superteam.
    public = github(api_path + "/public-key", pat)
    if not isinstance(public, dict) or not public.get("key") or not public.get("key_id"):
        raise BootstrapError("Could not obtain GitHub Actions secrets public key")
    existing = github(api_path + "/SUPERTEAM_API_KEY", pat, missing_ok=True)
    if existing is not None:
        raise BootstrapError("SUPERTEAM_API_KEY already exists. Refusing to create a duplicate agent.")

    print("Preflight passed; registering one Superteam agent...")
    api_key, claim_code, agent_id, username = register_agent()
    print("Superteam agent registration succeeded; saving encrypted GitHub secrets...")
    # Critical section: if saving fails, a new unclaimed Superteam agent may be orphaned.
    for secret_name, value in (("SUPERTEAM_API_KEY", api_key),
                               ("SUPERTEAM_CLAIM_CODE", claim_code)):
        github(api_path + "/" + secret_name, pat, method="PUT", payload={
            "encrypted_value": encrypt_for_github(value, public["key"]),
            "key_id": public["key_id"],
        })
        print(secret_name + " saved as an encrypted GitHub repository secret.")

    # Remove short-lived bootstrap PAT from repository after successful storage.
    # If deletion fails, user can remove it from Settings > Actions secrets.
    try:
        github(api_path + "/GH_BOOTSTRAP_PAT", pat, method="DELETE")
        print("GH_BOOTSTRAP_PAT removed from repository secrets.")
    except BootstrapError:
        print("WARNING: GH_BOOTSTRAP_PAT cleanup failed; delete the secret manually.")

    # Identifiers aren't credentials. Only share public metadata.
    print("Agent ready. ID: " + agent_id + " | username: " + username)
    print("Do NOT print or export SUPERTEAM_API_KEY or SUPERTEAM_CLAIM_CODE.")
    print("Claim code is stored as a secret for the future human-payout claim flow.")


if __name__ == "__main__":
    try:
        main()
    except BootstrapError as exc:
        print("BOOTSTRAP_ERROR: " + str(exc), file=sys.stderr)
        sys.exit(1)
