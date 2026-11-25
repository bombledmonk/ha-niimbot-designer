# Send one Home Assistant WebSocket command and print the result as JSON.
#
# The HA URL and a long-lived access token are read from a DPAPI-encrypted file
# (only this Windows user can decrypt it). Create it once with:
#   New-Item -ItemType Directory -Force "$env:USERPROFILE\.secrets" | Out-Null
#   Get-Credential -UserName "https://home.example.com" -Message "Paste your HA long-lived access token as the password" |
#     Export-Clixml "$env:USERPROFILE\.secrets\home-assistant.clixml"
#
# Usage: scripts/ha-ws.ps1 -Type niimbot_designer/list -Url https://home.example.com
#        scripts/ha-ws.ps1 -Type niimbot_designer/get -Fields @{ entry_id = "abc" }
param(
    [Parameter(Mandatory)][string]$Type,
    [hashtable]$Fields = @{},
    [string]$Url = $env:HA_URL,
    [string]$Secret = (Join-Path $env:USERPROFILE ".secrets\home-assistant.clixml"),
    [int]$Depth = 20
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Secret)) { throw "No HA token file at $Secret" }
$cred = Import-Clixml $Secret
# The HA address comes from -Url, then $env:HA_URL, then the credential's user name.
if (-not $Url -and $cred.UserName -match "^https?://") { $Url = $cred.UserName }
if (-not $Url) { throw "Pass -Url (or set HA_URL) with your Home Assistant address" }
$base = $Url.TrimEnd("/")
$wsUri = [Uri](($base -replace "^http", "ws") + "/api/websocket")

$ws = New-Object System.Net.WebSockets.ClientWebSocket
$ct = [Threading.CancellationToken]::None

function Receive-Message {
    $buf = New-Object byte[] 65536
    $ms = New-Object IO.MemoryStream
    do {
        $seg = New-Object ArraySegment[byte] -ArgumentList (, $buf)
        $r = $ws.ReceiveAsync($seg, $ct).GetAwaiter().GetResult()
        if ($r.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close) { throw "HA closed the connection" }
        $ms.Write($buf, 0, $r.Count)
    } while (-not $r.EndOfMessage)
    [Text.Encoding]::UTF8.GetString($ms.ToArray()) | ConvertFrom-Json
}

function Send-Message($obj) {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($obj | ConvertTo-Json -Compress -Depth $Depth))
    $seg = New-Object ArraySegment[byte] -ArgumentList (, $bytes)
    $null = $ws.SendAsync($seg, [Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).GetAwaiter().GetResult()
}

try {
    $null = $ws.ConnectAsync($wsUri, $ct).GetAwaiter().GetResult()
    $null = Receive-Message  # auth_required
    Send-Message @{ type = "auth"; access_token = $cred.GetNetworkCredential().Password }
    $auth = Receive-Message
    if ($auth.type -ne "auth_ok") { throw "HA auth failed: $($auth.message)" }

    $msg = @{ id = 1; type = $Type }
    foreach ($k in $Fields.Keys) { $msg[$k] = $Fields[$k] }
    Send-Message $msg
    do { $res = Receive-Message } while ($res.id -ne 1)
    if (-not $res.success) { throw "HA error: $($res.error.code) $($res.error.message)" }
    $res.result | ConvertTo-Json -Depth $Depth
} finally {
    if ($ws.State -eq [Net.WebSockets.WebSocketState]::Open) {
        $null = $ws.CloseAsync([Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "", $ct).GetAwaiter().GetResult()
    }
    $ws.Dispose()
}
