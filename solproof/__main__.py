"""SolProof: conservative read-only Solana payment evidence checker."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
DEFAULT_RPC = "https://api.mainnet-beta.solana.com"


class ProofError(Exception):
    pass


def decode58(value: str) -> bytes:
    if not value or any(c not in ALPHABET for c in value):
        raise ProofError("Invalid Base58 value")
    n = 0
    for c in value:
        n = 58 * n + ALPHABET.index(c)
    tail = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * (len(value) - len(value.lstrip("1"))) + tail


def validate_address(value: str) -> None:
    if len(decode58(value)) != 32:
        raise ProofError("Solana public address must decode to 32 bytes")


def get_transaction(signature: str, rpc_url: str):
    if len(decode58(signature)) != 64:
        raise ProofError("Signature must decode to 64 bytes")
    if not rpc_url.startswith("https://"):
        raise ProofError("RPC URL must use HTTPS")
    data = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction",
            "params": [signature, {"encoding": "jsonParsed", "commitment": "finalized",
                                   "maxSupportedTransactionVersion": 0}]}
    req = Request(rpc_url, method="POST", data=json.dumps(data).encode(),
                  headers={"Content-Type": "application/json", "User-Agent": "SolProof/0.1"})
    try:
        with urlopen(req, timeout=25) as res:
            response = json.loads(res.read(4_000_000))
    except HTTPError as exc:
        raise ProofError("RPC returned HTTP " + str(exc.code)) from None
    except (URLError, ValueError, OSError):
        raise ProofError("RPC did not return a valid response") from None
    if not isinstance(response, dict) or response.get("error"):
        raise ProofError("RPC returned a JSON-RPC error")
    return response.get("result")


def instructions(tx):
    for ix in tx["transaction"]["message"].get("instructions", []):
        if isinstance(ix, dict):
            yield ix
    for group in tx["meta"].get("innerInstructions") or []:
        for ix in group.get("instructions", []):
            if isinstance(ix, dict):
                yield ix


def token_balances(entries, owner, mint):
    total, indexes, decimals = 0, set(), set()
    for entry in entries:
        if entry.get("owner") != owner or entry.get("mint") != mint:
            continue
        amount = entry.get("uiTokenAmount") or {}
        val, dec, idx = amount.get("amount"), amount.get("decimals"), entry.get("accountIndex")
        if (not isinstance(val, str) or not val.isdecimal() or
                not isinstance(dec, int) or isinstance(dec, bool) or
                dec < 0 or dec > 18 or not isinstance(idx, int) or isinstance(idx, bool)):
            raise ProofError("Token metadata incomplete or invalid")
        total += int(val)
        indexes.add(idx)
        decimals.add(dec)
    if len(decimals) > 1:
        raise ProofError("Inconsistent decimals")
    return total, indexes, decimals


def evaluate(tx: dict | None, signature: str, recipient: str, mint: str = "SOL") -> dict:
    validate_address(recipient)
    if mint != "SOL":
        validate_address(mint)
    result = {"signature": signature, "recipient": recipient, "asset": mint,
              "network": "solana", "verified": False, "amount": "0",
              "slot": None, "reason": "Not found at finalized commitment"}
    if not isinstance(tx, dict):
        return result
    result["slot"] = tx.get("slot")
    meta = tx.get("meta")
    if not isinstance(meta, dict) or meta.get("err") is not None:
        result["reason"] = "Transaction failed or metadata missing"
        return result
    try:
        msg = tx["transaction"]["message"]
        keys = [key["pubkey"] if isinstance(key, dict) else key
                for key in msg["accountKeys"]]
        pre, post = meta["preBalances"], meta["postBalances"]
        if len(keys) != len(pre) or len(keys) != len(post):
            raise ProofError("Inconsistent account balances")
        ixs = list(instructions(tx))
        if mint == "SOL":
            matches = [i for i, key in enumerate(keys) if key == recipient]
            if len(matches) != 1:
                raise ProofError("Recipient account absent or ambiguous")
            delta = int(post[matches[0]]) - int(pre[matches[0]])
            explicit = 0
            for ix in ixs:
                parsed = ix.get("parsed") or {}
                info = parsed.get("info") or {}
                if ix.get("program") == "system" and parsed.get("type") == "transfer" and info.get("destination") == recipient:
                    lamports = info.get("lamports")
                    if not isinstance(lamports, int) or isinstance(lamports, bool) or lamports < 0:
                        raise ProofError("Invalid transfer amount")
                    explicit += lamports
            credited = max(0, min(delta, explicit))
            result["amount"] = str(Decimal(credited) / Decimal(10**9))
        else:
            before, _, before_dec = token_balances(meta.get("preTokenBalances") or [], recipient, mint)
            after, indices, after_dec = token_balances(meta.get("postTokenBalances") or [], recipient, mint)
            if not after_dec or (before_dec and before_dec != after_dec):
                raise ProofError("Missing token ownership or decimal metadata")
            dec = next(iter(after_dec))
            destinations = {keys[i] for i in indices if 0 <= i < len(keys)}
            explicit = 0
            for ix in ixs:
                parsed = ix.get("parsed") or {}
                info = parsed.get("info") or {}
                if (ix.get("program") in ("spl-token", "spl-token-2022")
                        and parsed.get("type") == "transferChecked"
                        and info.get("mint") == mint and info.get("destination") in destinations):
                    token_amt = info.get("tokenAmount") or {}
                    amount = token_amt.get("amount")
                    if (not isinstance(amount, str) or not amount.isdecimal()
                            or token_amt.get("decimals") != dec):
                        raise ProofError("Invalid transferChecked metadata")
                    explicit += int(amount)
            credited = max(0, min(after - before, explicit))
            result["amount"] = str(Decimal(credited) / (Decimal(10) ** dec))
        result["verified"] = credited > 0
        result["reason"] = ("Finalized explicit transfer and positive recipient net balance"
                            if credited else "No attributable positive recipient net transfer")
    except (KeyError, TypeError, ValueError, IndexError, ProofError):
        result["reason"] = "Insufficient parsed transaction evidence"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="SolProof: finalized payout evidence, read-only")
    parser.add_argument("--signature", required=True)
    parser.add_argument("--recipient", required=True)
    parser.add_argument("--mint", default="SOL")
    parser.add_argument("--min-amount", default="0")
    parser.add_argument("--rpc-url", default=os.environ.get("SOLANA_RPC_URL", DEFAULT_RPC))
    args = parser.parse_args(argv)
    try:
        minimum = Decimal(args.min_amount)
        if not minimum.is_finite() or minimum < 0:
            raise ProofError("Minimum must be finite and nonnegative")
        validate_address(args.recipient)
        if args.mint != "SOL":
            validate_address(args.mint)
        tx = get_transaction(args.signature, args.rpc_url)
        proof = evaluate(tx, args.signature, args.recipient, args.mint)
        proof["meets_minimum"] = proof["verified"] and Decimal(proof["amount"]) >= minimum
        proof["note"] = ("Evidence from the selected RPC, NOT proof of commercial "
                         "revenue, fiat value, token legitimacy or payer identity.")
        print(json.dumps(proof, indent=2))
        return 0 if proof["meets_minimum"] else 1
    except (InvalidOperation, ProofError) as exc:
        print(json.dumps({"verified": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
