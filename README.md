# Il Bot Scomodo — AKE Scout, Telegram & SolProof

Public, cost-controlled experiments toward **real earned income**. Maintained
with GitHub Actions; no laptop or private keys required for scheduled scans.
**Income earned by these tools: €0 as of 2026-10-10.** No bounties have been won.

## Modules

### 1. Superteam Earn Scout
- `python -m scout --create-issues --min-score 0` reads the official
  authenticated agent-eligible listings feed and opens up to 3 GitHub Issues
  per scan with raw rewards **unverified**.
- `.github/workflows/scout.yml` runs every 4 hours (best-effort).
- Scans create research leads, **not applications or earned rewards**.

### 2. Telegram operator interface
- Private Telegram bot: [@IlBotScomodo_bot](https://t.me/IlBotScomodo_bot).
- `/id` works during setup. After `TELEGRAM_OWNER_ID` is configured,
  `/status`, `/opportunita`, `/help`, and `/claim` are owner-restricted.
- `.github/workflows/telegram-bot.yml` polls at 10-minute intervals.
- `/claim` provides the sensitive Superteam claim link **only in private chats
  after checking the owner ID**. Telegram bot chats are not end-to-end encrypted.
- Never send wallet seed phrases, access tokens or signing instructions to bots.
- This bot is **read-only**, not a general AI chat or financial execution agent.

### 3. SolProof (working prototype)
- [Documentation and CLI examples](SOLPROOF.md)
- `python -m solproof --signature SIGNATURE --recipient PUBLIC_ADDRESS`
- Checks `finalized` Solana SOL and checked SPL transfers via JSON-RPC.
- Requires an explicit parsed transfer AND positive net recipient balance.
- Uses no private keys, no contracts, no funds and no external dependencies.
- Evidence checker, NOT certification that a bounty was won or income earned.

## Tests

    python -m unittest discover -s tests -v

GitHub Actions runs the tests on changes. Latest result at the time of
this update: **17 tests passed**. Source implementations still require
live public RPC cross-checking for representative real payout transactions.

## Current risks and boundaries
- This repository is public. Never add Secrets, private wallet addresses or
  personally identifiable account credentials to source files or Issues.
- No smart contracts deployed, no tokens launched, no ETH/SOL spending.
- A public Github issue is NOT customer demand or a confirmed commission.
- Access to a human Talent account, KYC or payout claim requires the human owner.
- GitHub Actions may run late; it is not a 24/7 live server.
- No automatic bidding or submissions that breach listing eligibility or quality.

## Docs
- [Superteam agent API](https://superteam.fun/earn/agents)
- [Solana RPC transactions](https://solana.com/docs/rpc/http/gettransaction)
- [SolProof user guide](SOLPROOF.md)
