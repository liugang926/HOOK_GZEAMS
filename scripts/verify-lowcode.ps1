param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Username = "admin",
  [string]$Password = "admin123",
  [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

function Assert-True([bool]$Cond, [string]$Msg) {
  if (-not $Cond) { throw $Msg }
}

function Invoke-Retry([scriptblock]$Fn, [int]$Retries = 20, [int]$DelayMs = 500) {
  for ($i = 0; $i -lt $Retries; $i++) {
    try { return & $Fn } catch {
      if ($i -eq ($Retries - 1)) { throw }
      Start-Sleep -Milliseconds $DelayMs
    }
  }
}

Write-Host "[verify-lowcode] login..."
$login = Invoke-Retry {
  Invoke-WebRequest -Uri "$BaseUrl/api/auth/login/" -Method POST -ContentType "application/json" -Body (@{ username = $Username; password = $Password } | ConvertTo-Json) -TimeoutSec 30
} -Retries 30 -DelayMs 500
$loginObj = $login.Content | ConvertFrom-Json
Assert-True ($loginObj.success -eq $true) "Login failed"
$token = $loginObj.data.token
Assert-True ([string]::IsNullOrWhiteSpace($token) -eq $false) "Missing access token"

$headers = @{ Authorization = "Bearer $token" }

Write-Host "[verify-lowcode] runtime contract..."
$runtime = Invoke-Retry {
  Invoke-WebRequest -Uri "$BaseUrl/api/system/objects/Asset/runtime/?mode=readonly" -Headers $headers -TimeoutSec 30
} -Retries 10 -DelayMs 500
$runtimeObj = $runtime.Content | ConvertFrom-Json
Assert-True ($runtimeObj.success -eq $true) "runtime endpoint failed"
Assert-True ($runtimeObj.data.runtimeVersion -eq 1) "runtimeVersion is not 1"
Assert-True ($null -ne $runtimeObj.data.fields) "runtime.fields missing"
Assert-True ($null -ne $runtimeObj.data.layout) "runtime.layout missing"

Write-Host "[verify-lowcode] user router..."
$userList = Invoke-Retry {
  Invoke-WebRequest -Uri "$BaseUrl/api/system/objects/User/?page=1&page_size=1" -Headers $headers -TimeoutSec 30
} -Retries 10 -DelayMs 500
$userObj = $userList.Content | ConvertFrom-Json
Assert-True ($userObj.success -eq $true) "User list failed"

Write-Host "[verify-lowcode] current user via object router..."
$me = Invoke-Retry {
  Invoke-WebRequest -Uri "$BaseUrl/api/system/objects/User/me/" -Headers $headers -TimeoutSec 30
} -Retries 10 -DelayMs 500
$meObj = $me.Content | ConvertFrom-Json
Assert-True ($meObj.success -eq $true) "User me failed"
Assert-True ([string]::IsNullOrWhiteSpace($meObj.data.username) -eq $false) "User me missing username"

Write-Host "[verify-lowcode] org router list shape..."
$orgList = Invoke-Retry {
  Invoke-WebRequest -Uri "$BaseUrl/api/system/objects/Organization/?page=1&page_size=1" -Headers $headers -TimeoutSec 30
} -Retries 10 -DelayMs 500
$orgObj = $orgList.Content | ConvertFrom-Json
Assert-True ($orgObj.success -eq $true) "Organization list failed"
Assert-True ($null -ne $orgObj.data.results) "Organization list is not paginated (missing data.results)"

if (-not $SkipFrontend) {
  Write-Host "[verify-lowcode] frontend smoke..."
  Push-Location (Join-Path $PSScriptRoot "..\\frontend")
  try {
    npm run test:e2e:smoke
    npm run build
  } finally {
    Pop-Location
  }
}

Write-Host "[verify-lowcode] OK"
