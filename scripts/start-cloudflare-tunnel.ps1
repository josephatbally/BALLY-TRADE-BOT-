[CmdletBinding()]
param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    throw "cloudflared was not found. Install it from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ and reopen PowerShell."
}

if (-not $SkipHealthCheck) {
    try {
        $health = Invoke-WebRequest -Uri "$($ApiUrl.TrimEnd('/'))/health" -TimeoutSec 5
        if ($health.StatusCode -lt 200 -or $health.StatusCode -ge 300) {
            throw "Health endpoint returned HTTP $($health.StatusCode)."
        }
        Write-Host "BALLY FLOW API health check passed ($($health.StatusCode))." -ForegroundColor Green
    }
    catch {
        throw "BALLY FLOW API is not responding at $ApiUrl/health. Start the existing backend first; this script will not launch a second Uvicorn process. Details: $($_.Exception.Message)"
    }
}

Write-Warning "Quick Tunnels are temporary and publicly reachable by anyone who knows the URL. Use only for controlled testing; do not expose trading controls unless backend authentication and authorization are working."
Write-Host "Starting temporary Cloudflare Tunnel to $ApiUrl. Keep this window open." -ForegroundColor Cyan
& $cloudflared.Source tunnel --url $ApiUrl
