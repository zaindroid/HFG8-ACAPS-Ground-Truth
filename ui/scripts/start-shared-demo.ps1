$ErrorActionPreference = 'Stop'
$uiRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$stateRoot = Join-Path $uiRoot '.demo-state'
New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
Push-Location $uiRoot
try {
  $buildLog = Join-Path $stateRoot 'build.log'
  npm run build:share *> $buildLog
  if ($LASTEXITCODE -ne 0) { Get-Content -LiteralPath $buildLog -Tail 35; throw 'The shared demo build failed.' }
  Write-Output 'Shared demo build ready.'

  $health = $null
  try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:4174/api/demo/health' -TimeoutSec 2 } catch { }
  if (-not $health -or $health.mode -ne 'shared-demo') {
    $server = Start-Process -FilePath 'node' -ArgumentList 'scripts/demo-server.mjs' -WorkingDirectory $uiRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $stateRoot 'server.log') -RedirectStandardError (Join-Path $stateRoot 'server-error.log')
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
      Start-Sleep -Milliseconds 500
      try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:4174/api/demo/health' -TimeoutSec 2; if ($health.mode -eq 'shared-demo') { $ready = $true; break } } catch { }
    }
    if (-not $ready) { throw "The demo server did not start. Check $stateRoot\server-error.log" }
    Write-Output "Demo server process: $($server.Id)"
  }

  $tunnel = $null
  try { $tunnel = (Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -TimeoutSec 2).tunnels | Where-Object { $_.public_url -like 'https://*' } | Select-Object -First 1 } catch { }
  if (-not $tunnel) {
    $agent = Start-Process -FilePath 'ngrok' -ArgumentList 'http','4174' -WorkingDirectory $uiRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $stateRoot 'ngrok.log') -RedirectStandardError (Join-Path $stateRoot 'ngrok-error.log')
    for ($i = 0; $i -lt 30; $i++) {
      Start-Sleep -Milliseconds 500
      try { $tunnel = (Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -TimeoutSec 2).tunnels | Where-Object { $_.public_url -like 'https://*' } | Select-Object -First 1; if ($tunnel) { break } } catch { }
    }
    if (-not $tunnel) { throw "ngrok did not start. Check $stateRoot\ngrok-error.log" }
    Write-Output "ngrok process: $($agent.Id)"
  }
  Write-Output "Public demo: $($tunnel.public_url)"
  $codeFile = Join-Path $stateRoot 'access-code.txt'
  if (Test-Path -LiteralPath $codeFile) { Write-Output "Analyst access code: $((Get-Content -LiteralPath $codeFile -Raw).Trim())" }
  else { Write-Output 'Analyst access code: see the running server terminal' }
  Write-Output 'Keep this computer awake during the demo. Guests may need to click Visit Site on the first ngrok visit.'
} finally { Pop-Location }
