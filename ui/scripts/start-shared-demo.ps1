$ErrorActionPreference = 'Stop'
$uiRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$stateRoot = Join-Path $uiRoot '.demo-state'
New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
Push-Location $uiRoot
try {
  $buildLog = Join-Path $stateRoot 'build.log'
  $buildErrorLog = Join-Path $stateRoot 'build-error.log'
  $build = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','build:share' -WorkingDirectory $uiRoot -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrorLog
  if ($build.ExitCode -ne 0) { Get-Content -LiteralPath $buildLog -Tail 35; Get-Content -LiteralPath $buildErrorLog -Tail 20; throw 'The shared demo build failed.' }
  Write-Output 'Shared demo build ready.'

  $engineRoot = (Resolve-Path -LiteralPath (Join-Path $uiRoot '..\engine')).Path
  $enginePython = Join-Path $engineRoot '.venv\Scripts\python.exe'
  if (-not (Test-Path -LiteralPath $enginePython)) { throw 'The trust engine is not installed. Run: uv venv engine/.venv --python 3.12; uv pip install --python engine/.venv/Scripts/python.exe -r engine/requirements.txt' }
  $engineHealth = $null
  try { $engineHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:18000/health' -TimeoutSec 2 } catch { }
  if (-not $engineHealth -or $engineHealth.status -ne 'ok') {
    $secretFile = Join-Path $stateRoot 'engine-secrets.json'
    if (Test-Path -LiteralPath $secretFile) { $secrets = Get-Content -LiteralPath $secretFile -Raw | ConvertFrom-Json }
    else {
      $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
      try {
        $values = @()
        for ($i = 0; $i -lt 3; $i++) { $bytes = New-Object byte[] 32; $generator.GetBytes($bytes); $values += ([BitConverter]::ToString($bytes)).Replace('-','').ToLowerInvariant() }
        $secrets = [pscustomobject]@{ commitment=$values[0]; pseudonym=$values[1]; committee=$values[2] }
        $secrets | ConvertTo-Json -Compress | Set-Content -LiteralPath $secretFile -Encoding utf8
      } finally { $generator.Dispose() }
    }
    $env:COMMITMENT_SALT = $secrets.commitment
    $env:PSEUDONYM_KEY = $secrets.pseudonym
    $env:COMMITTEE_KEY = $secrets.committee
    $env:APP_ENV = 'development'
    $env:FF_PQ = '1'; $env:FF_BLIND = '1'; $env:FF_ANCHOR = '1'; $env:FF_E2E = '1'; $env:FF_CHAIN = '1'
    $engine = Start-Process -FilePath $enginePython -ArgumentList '-m','uvicorn','engine.api:app','--host','127.0.0.1','--port','18000' -WorkingDirectory $engineRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $stateRoot 'engine.log') -RedirectStandardError (Join-Path $stateRoot 'engine-error.log')
    for ($i = 0; $i -lt 30; $i++) {
      Start-Sleep -Milliseconds 500
      try { $engineHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:18000/health' -TimeoutSec 2; if ($engineHealth.status -eq 'ok') { break } } catch { }
    }
    if (-not $engineHealth -or $engineHealth.status -ne 'ok') { throw "The trust engine did not start. Check $stateRoot\engine-error.log" }
    Write-Output "Trust engine process: $($engine.Id)"
  }

  $health = $null
  try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:4174/api/demo/health' -TimeoutSec 2 } catch { }
  if (-not $health -or $health.mode -ne 'shared-demo') {
    $codeFile = Join-Path $stateRoot 'access-code.txt'
    if (Test-Path -LiteralPath $codeFile) { $env:DEMO_ACCESS_CODE = (Get-Content -LiteralPath $codeFile -Raw).Trim() }
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
