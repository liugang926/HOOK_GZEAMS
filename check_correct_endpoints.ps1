# Check Backend API Endpoints Availability - Corrected Version

$BASE_URL = "http://localhost:8000/api"
$USERNAME = "admin"
$PASSWORD = "admin123"

# Function to make HTTP request
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Token
    )

    try {
        $headers = @{
            "Authorization" = "Bearer $Token"
            "Content-Type" = "application/json"
        }

        $response = Invoke-RestMethod -Uri $Url -Method Get -Headers $headers -ErrorAction Stop
        return @{
            StatusCode = 200
            Success = $true
            Response = $response
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__

        return @{
            StatusCode = $statusCode
            Success = $false
            Response = $_.Exception.Message
        }
    }
}

# Step 1: Login
Write-Host "=" * 80
Write-Host "Step 1: Authenticating..."
Write-Host "=" * 80

$loginUrl = "$BASE_URL/auth/login/"
$loginBody = @{
    username = $USERNAME
    password = $PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri $loginUrl -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.data.token
    Write-Host "[OK] Login successful! Token: $($token.Substring(0, [Math]::Min(50, $token.Length)))..."
}
catch {
    Write-Host "[ERROR] Login failed: $_"
    exit 1
}

# Step 2: Test endpoints
Write-Host ""
Write-Host "=" * 80
Write-Host "Step 2: Testing API Endpoints (Corrected URLs)"
Write-Host "=" * 80

$endpoints = @(
    # Assets endpoints
    @{ Path = "/assets/"; Name = "Assets (Main)"; Expected = 200 },
    @{ Path = "/assets/categories/"; Name = "Asset Categories"; Expected = 200 },
    @{ Path = "/assets/suppliers/"; Name = "Suppliers"; Expected = 200 },
    @{ Path = "/assets/locations/"; Name = "Locations"; Expected = 200 },

    # Organizations endpoints
    @{ Path = "/organizations/departments/"; Name = "Departments"; Expected = 200 },

    # Consumables endpoints
    @{ Path = "/consumables/"; Name = "Consumables (Main)"; Expected = 200 },
    @{ Path = "/consumables/consumables/"; Name = "Consumables List"; Expected = 200 },

    # Inventory endpoints
    @{ Path = "/inventory/tasks/"; Name = "Inventory Tasks"; Expected = 200 },

    # Lifecycle/Maintenance endpoints
    @{ Path = "/lifecycle/maintenance/"; Name = "Maintenance Records"; Expected = 200 }
)

$results = @()

foreach ($endpoint in $endpoints) {
    Write-Host ""
    Write-Host ("-" * 80)
    Write-Host "Testing: $($endpoint.Name) - $($endpoint.Path)"
    Write-Host ("-" * 80)

    $url = "$BASE_URL$($endpoint.Path)"
    $result = Test-Endpoint -Url $url -Token $token

    Write-Host "URL: $url"
    Write-Host "Status Code: $($result.StatusCode)"

    if ($result.StatusCode -eq $endpoint.Expected) {
        $status = "[OK] Working ($($result.StatusCode))"
    }
    elseif ($result.StatusCode -eq 401) {
        $status = "[WARN] Exists but Unauthorized (401)"
    }
    elseif ($result.StatusCode -eq 400) {
        $status = "[WARN] Exists but Bad Request (400)"
    }
    elseif ($result.StatusCode -eq 404) {
        $status = "[MISSING] Not Found (404)"
    }
    elseif ($result.StatusCode -eq 405) {
        $status = "[WARN] Exists but Method Not Allowed (405)"
    }
    else {
        $status = "[WARN] Unexpected ($($result.StatusCode))"
    }

    Write-Host "Status: $status"

    $results += @{
        Name = $endpoint.Name
        Path = $endpoint.Path
        StatusCode = $result.StatusCode
        Status = $status
        Expected = $endpoint.Expected
    }
}

# Step 3: Summary
Write-Host ""
Write-Host "=" * 80
Write-Host "Step 3: Summary"
Write-Host "=" * 80

$working = $results | Where-Object { $_.StatusCode -eq $_.Expected }
$missing = $results | Where-Object { $_.StatusCode -eq 404 }
$wrongStatus = $results | Where-Object { $_.StatusCode -ne $_.Expected -and $_.StatusCode -ne 404 }

Write-Host ""
Write-Host "[OK] Working Endpoints ($($working.Count)):"
foreach ($r in $working) {
    Write-Host "  [+] $($r.Name.PadRight(30)) $($r.Path.PadRight(35)) $($r.Status)"
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "[MISSING] Missing Endpoints ($($missing.Count)):"
    foreach ($r in $missing) {
        Write-Host "  [-] $($r.Name.PadRight(30)) $($r.Path.PadRight(35)) $($r.Status)"
    }
}

if ($wrongStatus.Count -gt 0) {
    Write-Host ""
    Write-Host "[WARN] Wrong Status Endpoints ($($wrongStatus.Count)):"
    foreach ($r in $wrongStatus) {
        Write-Host "  [!] $($r.Name.PadRight(30)) $($r.Path.PadRight(35)) $($r.Status)"
    }
}

Write-Host ""
Write-Host "=" * 80
Write-Host "Total: $($results.Count) endpoints tested"
Write-Host "Working: $($working.Count)"
Write-Host "Missing: $($missing.Count)"
Write-Host "Wrong Status: $($wrongStatus.Count)"
Write-Host "=" * 80

# Step 4: URL Configuration Analysis
Write-Host ""
Write-Host "=" * 80
Write-Host "Step 4: URL Configuration Summary"
Write-Host "=" * 80

Write-Host ""
Write-Host "URL Configuration Locations:"
Write-Host "  Main Config: backend/config/urls.py"
Write-Host "  Assets:       backend/apps/assets/urls.py"
Write-Host "  Organizations: backend/apps/organizations/urls.py"
Write-Host "  Consumables:  backend/apps/consumables/urls.py"
Write-Host "  Inventory:    backend/apps/inventory/urls.py"
Write-Host "  Lifecycle:    backend/apps/lifecycle/urls.py"
Write-Host ""
Write-Host "URL Mapping:"
Write-Host "  /assets/                    -> AssetViewSet (main asset list)"
Write-Host "  /assets/categories/         -> AssetCategoryViewSet"
Write-Host "  /assets/suppliers/          -> SupplierViewSet"
Write-Host "  /assets/locations/          -> LocationViewSet"
Write-Host "  /organizations/departments/ -> DepartmentViewSet"
Write-Host "  /consumables/               -> ConsumableViewSet (empty path)"
Write-Host "  /consumables/consumables/   -> ConsumableViewSet (explicit path)"
Write-Host "  /inventory/tasks/           -> InventoryTaskViewSet"
Write-Host "  /lifecycle/maintenance/     -> MaintenanceViewSet"
