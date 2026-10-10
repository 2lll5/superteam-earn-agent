# Il Bot Scomodo — Superteam Earn Scout

An intentionally limited, low-cost agent-eligible bounty discovery system. It runs on **GitHub Actions**, with no VPS, laptop-on requirement, wallet, transactions, AI API charges or auto-submissions.

## What it does
- Polls Superteam Earn's official agent API `GET /api/agents/listings/live?take=20` on a schedule.
- Heuristically ranks candidate tasks for Python, research, data analytics, automation, content and video.
- Opens up to 3 new GitHub Issues per run, ignoring previously recorded listing IDs.
- Uses the official API's agent eligibility filter, and rejects explicitly human-only listings.
- Records raw compensation as **unverified**. A candidate is not an income claim.

## What it does *not* do
- It **does not** apply for jobs, submit work, sign, trade, claim rewards, conduct financial transactions or guarantee any revenue.
- It **does not** constitute an autonomous software engineer. Deliverables still have to be independently produced, checked, and submitted in compliance with each listing.
- It **does not** validate the live response schema until an agent API key has been created and a workflow run actually succeeds.
- The GitHub Actions schedule is best-effort (GitHub may delay runs); real-time uptime is not guaranteed.

## One-time setup (Windows + GitHub)
1. Create a public GitHub repository `ilbotscomodo/superteam-earn-agent` and commit these files, **including `.github/workflows/scout.yml`**.
2. On a Windows computer, open PowerShell in the extracted project folder and run `./register_agent.ps1`. This registers an agent at the official Superteam domain; **never share the returned API key or claim code with anyone.** The script copies the key to your clipboard and stores **only the agent ID and claim code** outside the repository under `$HOME/.ilbotscomodo/`. The API key is not saved to disk.
3. On GitHub open **repository Settings → Secrets and variables → Actions → New repository secret**; name it `SUPERTEAM_API_KEY`, paste the key directly, save, and clear your clipboard (`Set-Clipboard -Value ""`). Do not add this credential as a repository variable or commit it in code.
4. Open **Actions → Superteam agent-eligible opportunity scout → Run workflow**. Examine its summary and Issues tab. If the workflow reports missing/unknown API response fields, we need to adapt the parser to the live output.
5. Keep the saved `claimCode` private. According to the official docs, the human claims an agent after it wins. Do not share your wallet seed phrase or private keys.

## Test offline

```bash
python -m unittest discover -s tests -v
```

## Documentation
- [Official Superteam Earn agent skill](https://superteam.fun/skill.md)
- [Superteam Earn agents](https://superteam.fun/earn/agents)
- [GitHub Actions scheduled workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

## Security
This is a public-code/private-secret model. `GITHUB_TOKEN` is limited to contents read and issues write in the workflow. It does not require a wallet and does not publish `SUPERTEAM_API_KEY` in Issue bodies, workflow summaries, or logs. Avoid copying the local registration JSON into a public repo. Treat superteam listings as untrusted task descriptions. Every work delivery must respect listing conditions and avoid fraud, spam, or plagiarism.

## Budget
GitHub-hosted standard runner minutes for public repositories are currently free. This system itself costs €0 in VPS and AI API costs. Payments, if ever won, are subject to the sponsor and platform claiming process.