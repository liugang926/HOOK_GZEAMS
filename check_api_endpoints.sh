#!/bin/bash

# Check Backend API Endpoints Availability

BASE_URL="http://localhost:8000/api"
USERNAME="admin"
PASSWORD="admin123"

echo "=============================================================================="
echo "Step 1: Authenticating..."
echo "=============================================================================="

# Login
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

echo "Login Response: $LOGIN_RESPONSE"

# Extract token using grep/sed (simple approach)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to extract token. Trying alternative..."
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token": "[^"]*"' | sed 's/"token": "\([^"]*\)"/\1/')
fi

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed or token not found"
    echo "Full response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful! Token: ${TOKEN:0:50}..."

echo ""
echo "=============================================================================="
echo "Step 2: Testing API Endpoints"
echo "=============================================================================="

# Array of endpoints
declare -a ENDPOINTS=(
    "/assets/:资产卡片"
    "/asset-categories/:资产分类"
    "/suppliers/:供应商"
    "/locations/:存放地点"
    "/departments/:部门"
    "/consumables/:低值易耗品"
    "/inventory-tasks/:盘点任务"
    "/maintenance/:维修记录"
)

# Results
WORKING=0
MISSING=0
ERRORS=0

for item in "${ENDPOINTS[@]}"; do
    endpoint="${item%%:*}"
    name="${item##*:}"

    echo ""
    echo "──────────────────────────────────────────────────────────────────────────────"
    echo "Testing: $name - $endpoint"
    echo "──────────────────────────────────────────────────────────────────────────────"

    url="${BASE_URL}${endpoint}"

    # Make request and capture status
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$url" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json")

    # Split response and status code
    STATUS_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)

    echo "URL: $url"
    echo "Status Code: $STATUS_CODE"
    echo "Response: ${BODY:0:200}"

    # Determine status
    if [ "$STATUS_CODE" = "200" ]; then
        STATUS="✅ Working (200)"
        WORKING=$((WORKING + 1))
    elif [ "$STATUS_CODE" = "401" ]; then
        STATUS="⚠️  Exists but Unauthorized (401)"
        WORKING=$((WORKING + 1))
    elif [ "$STATUS_CODE" = "400" ]; then
        STATUS="⚠️  Exists but Bad Request (400)"
        WORKING=$((WORKING + 1))
    elif [ "$STATUS_CODE" = "404" ]; then
        STATUS="❌ Not Found (404)"
        MISSING=$((MISSING + 1))
    elif [ "$STATUS_CODE" = "405" ]; then
        STATUS="⚠️  Exists but Method Not Allowed (405)"
        WORKING=$((WORKING + 1))
    else
        STATUS="⚠️  Unexpected ($STATUS_CODE)"
        ERRORS=$((ERRORS + 1))
    fi

    echo "Status: $STATUS"
done

echo ""
echo "=============================================================================="
echo "Step 3: Summary"
echo "=============================================================================="
echo ""
echo "Total endpoints tested: $((WORKING + MISSING + ERRORS))"
echo "Working: $WORKING"
echo "Missing: $MISSING"
echo "Errors: $ERRORS"
echo "=============================================================================="
