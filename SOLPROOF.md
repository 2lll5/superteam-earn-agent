# SolProof — verify Solana payouts without private keys

SolProof is an **open-source, read-only** proof-of-payment evidence CLI for Solana.
It checks that a **finalized** transaction includes an explicit native SOL or SPL
`transferChecked` credit to the requested receiver, and that the receiver's
net balance actually increased. It does **not** interact with wallets, sign or
broadcast transactions, deploy contracts, spend funds or hold crypto.

## Usage (Python 3.10+, no external dependencies)

    python -m solproof --signature SIGNATURE --recipient PUBLIC_SOLANA_ADDRESS --min-amount 0.1

For SPL token: add `--mint MINT_ADDRESS` and the expected `--min-amount`.
Default asset is SOL; you must supply the exact mint for SPL tokens.
Custom RPC endpoint: `--rpc-url https://your-rpc` or `SOLANA_RPC_URL`.
The default Solana public RPC may rate-limit requests; an HTTP 429 does not
prove nonpayment. Use reputable, independent RPCs for material sums.

Exit codes: 0 evidence meets amount, 1 not proven, 2 RPC/input failure.
JSON output explicitly states limits and avoids calling blockchain evidence
commercial revenue. Unknown/incomplete token metadata fails closed.

## Tests

    python -m unittest discover -s tests -v

## Limits & safety

- Evidence is RPC-provider-dependent, NOT an independently validated ledger.
- A `verified: true` result is **not** proof a bounty was won or a payment
  is legitimate, withdrawable, valued in EUR, or sent by a particular payer.
- Requires parsed explicit `system.transfer` or `spl-token.transferChecked`.
- SPL transfer must point to a token account owned by the named recipient.
- Conservative amount = min(parsed incoming transfers, recipient net increase).
- Complex transactions may be under-counted; unknown transfers are rejected.
- Tokens cannot be assumed to be USDG or USDC by name; check exact mint.
- Do not publish personally sensitive wallet transaction trails by default.
- This prototype supports legacy and version-0 parsed transactions.
- It is not audited for custodial or financial applications.

## Monetization hypothesis (not current revenue)

Offer custom payment reporting, cross-RPC verification or open-source
integrations to developers and AI-agent operators. No customer or payment
has been obtained; do not imply otherwise.

Official RPC documentation:
https://solana.com/docs/rpc/http/gettransaction
https://solana.com/docs/rpc/json-structures
