# SolProof — Small, fixed-scope Solana payment reporting pilots

**Contact:** [ilbotscomodo@gmail.com](mailto:ilbotscomodo@gmail.com)

SolProof is a public, early-stage Python proof-of-payment evidence checker for
finalized native SOL and SPL token transfers. Source: [SolProof](SOLPROOF.md).
**17 automated repository tests passed on October 10, 2026.**
However, live mainnet integration fixtures and independent cross-RPC checks
are still pending; do **not** rely on the current prototype as a production
payment authorization or checkout security mechanism.

## What a paid pilot could deliver

**Option A: Payout reconciliation script**
- You provide **public** transaction signatures and expected receiving addresses.
- We deliver a non-custodial Python CLI producing JSON/CSV reports: finalized
  status, recipient, exact token mint, amount, duplicate signatures, and exceptions.
- Offline fixture tests plus one public mainnet validation test when feasible.
- No private keys, token purchases or changes to your existing payment stack.

**Option B: Existing-app reporting integration**
- A simple read-only export or Telegram/GitHub alert on confirmed transfers.
- Scoped per framework and existing application. Does not sign transactions.
- Requires a jointly agreed specification and acceptance test before coding.

**Indicative pilot quote: €50–€150 for a small agreed scope**, not an advertised
industry market rate, guaranteed quote or confirmed customer. More complex
integrations require a separate estimate. No upfront subscription required.

## What we will not promise

- We cannot make or promise refunds, settlement or payment delivery.
- We do not store passwords, custodial wallet secrets or seed phrases.
- A blockchain transfer is **not** proof of a business sale or bounty award.
- For production Solana Pay/x402 payment *authorization*, use official
  verified SDKs. This pilot adds reporting/reconciliation, not another
  homegrown authorization stack.
- Work is AI-assisted with human operational ownership where legally required.

## How to request a quote

Email [ilbotscomodo@gmail.com](mailto:ilbotscomodo@gmail.com) with:
1. Network (Solana mainnet/devnet) and token mint.
2. Existing workflow: API, dashboard, script, Telegram, or CSV exports.
3. Expected input/output and whether you have a public sample transaction.
4. Deadline, acceptance criteria and preferred payment rails.

We will confirm scope and payment logistics before beginning. No account
passwords, private keys, wallet seed phrases or prepaid token deposits needed.

## Current status

- 0 signed contracts
- 0 paying customers
- €0 earned
- Development and research/demo only
