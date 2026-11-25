# Rebuild the niimblue fork (home-assistant branch) and copy it into the integration.
# Usage: scripts/update-frontend.ps1 [-Fork C:\dev\niimblue]
param([string]$Fork = (Join-Path $PSScriptRoot "..\..\niimblue"))

$www = Join-Path $PSScriptRoot "..\custom_components\niimbot_designer\www"

# npm writes warnings to stderr, so check exit codes instead of using ErrorActionPreference=Stop.
function Invoke-Native([scriptblock]$Cmd, [string]$What) {
    & $Cmd
    if ($LASTEXITCODE -ne 0) { throw "$What failed (exit $LASTEXITCODE)" }
}

Push-Location $Fork
try {
    if ((git rev-parse --abbrev-ref HEAD) -ne "home-assistant") { throw "Fork is not on the home-assistant branch" }
    if (git status --porcelain) { throw "Fork has uncommitted changes" }
    Invoke-Native { npm ci --no-audit --no-fund } "npm ci"
    $env:COMMIT_HASH = git rev-parse HEAD
    Invoke-Native { npm run build-rel } "build"
    $commit = $env:COMMIT_HASH
} finally {
    Pop-Location
}

# Keep the test page; replace everything else with the fresh build.
Get-ChildItem $www | Where-Object { $_.Name -ne "test.html" } | Remove-Item -Recurse -Force -Confirm:$false
Copy-Item -Recurse (Join-Path $Fork "dist\*") $www
Copy-Item (Join-Path $Fork "LICENSE") (Join-Path $www "LICENSE-niimblue.txt")
Set-Content -Path (Join-Path $www "FRONTEND_COMMIT") -Value $commit -Encoding ascii
"Frontend updated to fork commit $commit"
