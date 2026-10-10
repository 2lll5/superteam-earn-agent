# Run ONCE in PowerShell on your own Windows PC.
# NEVER paste the returned key, output file, or claim code in a chat or public GitHub repository.
$ErrorActionPreference = 'Stop'
$uri = 'https://superteam.fun/api/agents'
$agentName = 'Il Bot Scomodo Scout'
$response = Invoke-RestMethod -Uri $uri -Method POST -ContentType 'application/json' -Body (@{ name = $agentName } | ConvertTo-Json)
$agent = if ($response.data -and $response.data.apiKey) { $response.data } else { $response }
if (-not $agent.apiKey -or -not $agent.claimCode) {
  throw 'API did not return expected apiKey and claimCode; inspect locally, never publish raw response.'
}
$dir = Join-Path $HOME '.ilbotscomodo'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$privatePath = Join-Path $dir 'superteam-agent-private.json'
@{ agentId = $agent.agentId; username = $agent.username; claimCode = $agent.claimCode } | ConvertTo-Json -Depth 3 | Set-Content -Path $privatePath -Encoding UTF8
Set-Clipboard -Value $agent.apiKey
Write-Host 'Agent registered. The API key is currently on your Windows clipboard.'
Write-Host 'Paste it directly into GitHub repository Settings > Secrets and variables > Actions > New repository secret.'
Write-Host 'Secret name: SUPERTEAM_API_KEY'
Write-Host 'Claim code saved locally; do not expose it. The API key was NOT saved to disk.'
Write-Host ('Private local file: ' + $privatePath)
Write-Host 'Clear clipboard after pasting it by running: Set-Clipboard -Value ""'
