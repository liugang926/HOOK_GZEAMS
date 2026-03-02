param(
  [string]$ObjectCode = 'Asset',
  [string]$Mode = 'edit',
  [string]$BaseUrl = 'http://localhost:8000'
)

$login = Invoke-RestMethod -Uri "$BaseUrl/api/auth/login/" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}' -TimeoutSec 15
$token = $login.data.token
$orgId = $login.data.user.currentOrganization
$headers = @{ Authorization = "Bearer $token"; 'X-Organization-ID' = $orgId }

Write-Output "== Active layout =="
$active = Invoke-RestMethod -Uri "$BaseUrl/api/system/page-layouts/get_active_layout/?object_code=$ObjectCode&mode=$Mode" -Headers $headers -TimeoutSec 20
$activeConfig = $active.data.layoutConfig
$activeSections = if ($activeConfig.sections) { $activeConfig.sections.Count } else { 0 }
Write-Output "sections=$activeSections"

Write-Output "== Default layout =="
$default = Invoke-RestMethod -Uri "$BaseUrl/api/system/page-layouts/default/$ObjectCode/$Mode/" -Headers $headers -TimeoutSec 20
$defaultConfig = $default.data.layoutConfig
$defaultSections = if ($defaultConfig.sections) { $defaultConfig.sections.Count } else { 0 }
Write-Output "sections=$defaultSections"
