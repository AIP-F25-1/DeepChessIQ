#!/bin/bash

# API Testing Script with Performance Monitoring
BASE_URL="http://localhost:3000"
TEST_EMAIL="testapi@example.com"
TEST_PASSWORD="test123"

echo "=========================================="
echo "Testing DeepChessIQ Backend APIs"
echo "With Detailed Performance Metrics"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Performance tracking arrays
declare -a ENDPOINT_NAMES
declare -a RESPONSE_TIMES
declare -a HTTP_CODES
declare -a DNS_TIMES
declare -a CONNECT_TIMES
declare -a TRANSFER_TIMES

# Function to format time in milliseconds
format_time() {
    local time_seconds=$1
    local time_ms=$(echo "$time_seconds * 1000" | bc -l | awk '{printf "%.2f", $1}')
    echo "$time_ms"
}

# Function to get performance color
get_perf_color() {
    local time_ms=$1
    if (( $(echo "$time_ms < 100" | bc -l) )); then
        echo "$GREEN"
    elif (( $(echo "$time_ms < 500" | bc -l) )); then
        echo "$YELLOW"
    else
        echo "$RED"
    fi
}

# Function to test endpoint with performance metrics
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    local description=$5
    
    echo -e "${CYAN}Testing: $description${NC}"
    echo -n "  "
    
    # Create temp file for curl output
    local temp_file=$(mktemp)
    local temp_timing=$(mktemp)
    
    # Build curl command with timing
    local curl_cmd="curl -s -w \"\n%{http_code}\n%{time_namelookup}\n%{time_connect}\n%{time_starttransfer}\n%{time_total}\" -X $method \"$BASE_URL$endpoint\" -H \"Content-Type: application/json\""
    
    if [ -n "$token" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $token\""
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    # Execute curl and capture output
    eval "$curl_cmd" > "$temp_file" 2>&1
    
    # Parse response - curl outputs body first, then timing info
    local response=$(cat "$temp_file")
    local line_count=$(echo "$response" | wc -l | tr -d ' ')
    
    # Extract metrics from last 5 lines
    local http_code=$(echo "$response" | tail -n 5 | head -n 1)
    local dns_time=$(echo "$response" | tail -n 4 | head -n 1)
    local connect_time=$(echo "$response" | tail -n 3 | head -n 1)
    local transfer_time=$(echo "$response" | tail -n 2 | head -n 1)
    local total_time=$(echo "$response" | tail -n 1)
    
    # Extract body (everything except last 5 lines) - macOS compatible
    if [ "$line_count" -gt 5 ]; then
        local body=$(echo "$response" | sed -n "1,$((line_count-5))p" | tr '\n' ' ')
    else
        local body=""
    fi
    
    # Convert times to milliseconds
    local dns_ms=$(format_time "$dns_time")
    local connect_ms=$(format_time "$connect_time")
    local transfer_ms=$(format_time "$transfer_time")
    local total_ms=$(format_time "$total_time")
    
    # Store performance data
    ENDPOINT_NAMES+=("$description")
    RESPONSE_TIMES+=("$total_ms")
    HTTP_CODES+=("$http_code")
    DNS_TIMES+=("$dns_ms")
    CONNECT_TIMES+=("$connect_ms")
    TRANSFER_TIMES+=("$transfer_ms")
    
    # Get performance color
    local perf_color=$(get_perf_color "$total_ms")
    
    # Display results
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        echo -e "  ${BLUE}Performance Metrics:${NC}"
        echo -e "    Total Time:     ${perf_color}${total_ms}ms${NC}"
        echo -e "    DNS Lookup:     ${CYAN}${dns_ms}ms${NC}"
        echo -e "    Connect Time:    ${CYAN}${connect_ms}ms${NC}"
        echo -e "    Transfer Start:  ${CYAN}${transfer_ms}ms${NC}"
        ((PASSED++))
        rm -f "$temp_file" "$temp_timing"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo -e "  ${BLUE}Performance Metrics:${NC}"
        echo -e "    Total Time:     ${perf_color}${total_ms}ms${NC}"
        echo -e "    DNS Lookup:     ${CYAN}${dns_ms}ms${NC}"
        echo -e "    Connect Time:    ${CYAN}${connect_ms}ms${NC}"
        echo -e "    Transfer Start:  ${CYAN}${transfer_ms}ms${NC}"
        echo "  Response: ${body:0:100}..."
        ((FAILED++))
        rm -f "$temp_file" "$temp_timing"
        return 1
    fi
}

# 1. Health Check
echo "1. Health Check Endpoint"
test_endpoint "GET" "/healthz" "" "" "Health Check"
echo ""

# 2. Authentication
echo "2. Authentication Endpoints"
echo "   Signing up test user..."

# Test signup with performance
signup_temp=$(mktemp)
signup_response=$(curl -s -w "\n%{http_code}\n%{time_total}" -X POST "$BASE_URL/auth/signup" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"displayName\":\"API Test User\"}" > "$signup_temp" 2>&1)

signup_output=$(cat "$signup_temp")
signup_line_count=$(echo "$signup_output" | wc -l | tr -d ' ')
signup_http=$(echo "$signup_output" | tail -n 2 | head -n 1)
signup_time=$(echo "$signup_output" | tail -n 1)
if [ "$signup_line_count" -gt 2 ]; then
    signup_body=$(echo "$signup_output" | sed -n "1,$((signup_line_count-2))p" | tr '\n' ' ')
else
    signup_body=""
fi

signup_time_ms=$(format_time "$signup_time")
signup_color=$(get_perf_color "$signup_time_ms")

echo -e "  ${CYAN}Signup Performance:${NC} ${signup_color}${signup_time_ms}ms${NC} (HTTP $signup_http)"

# Extract token from signup body
TOKEN=$(echo "$signup_body" | grep -o '"token":"[^"]*' | cut -d'"' -f4 || echo "")

if [ -z "$TOKEN" ]; then
    echo "   Trying login instead..."
    login_temp=$(mktemp)
    login_response=$(curl -s -w "\n%{http_code}\n%{time_total}" -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" > "$login_temp" 2>&1)
    
    login_output=$(cat "$login_temp")
    login_line_count=$(echo "$login_output" | wc -l | tr -d ' ')
    login_http=$(echo "$login_output" | tail -n 2 | head -n 1)
    login_time=$(echo "$login_output" | tail -n 1)
    if [ "$login_line_count" -gt 2 ]; then
        login_body=$(echo "$login_output" | sed -n "1,$((login_line_count-2))p" | tr '\n' ' ')
    else
        login_body=""
    fi
    
    login_time_ms=$(format_time "$login_time")
    login_color=$(get_perf_color "$login_time_ms")
    
    echo -e "  ${CYAN}Login Performance:${NC} ${login_color}${login_time_ms}ms${NC} (HTTP $login_http)"
    
    TOKEN=$(echo "$login_body" | grep -o '"token":"[^"]*' | cut -d'"' -f4 || echo "")
    rm -f "$login_temp"
fi

rm -f "$signup_temp"

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Failed to get authentication token${NC}"
    exit 1
fi

echo -e "   ${GREEN}✓ Authentication successful${NC}"
echo "   Token: ${TOKEN:0:50}..."
echo ""

# 3. Profile API
echo "3. Profile API"
test_endpoint "GET" "/api/profile" "" "$TOKEN" "GET Profile"
test_endpoint "PUT" "/api/profile" '{"displayName":"Updated Name","bio":"Test bio","country":"USA"}' "$TOKEN" "UPDATE Profile"
echo ""

# 4. Settings API
echo "4. Settings API"
test_endpoint "GET" "/api/settings" "" "$TOKEN" "GET Settings"
test_endpoint "PUT" "/api/settings" '{"game":{"showLegalMoves":false,"highlightLastMove":true}}' "$TOKEN" "UPDATE Settings"
echo ""

# 5. Statistics API
echo "5. Statistics API"
test_endpoint "GET" "/api/statistics" "" "$TOKEN" "GET Statistics"
test_endpoint "GET" "/api/statistics/ratings/history?limit=10" "" "$TOKEN" "GET Rating History"
echo ""

# 6. Games API
echo "6. Games API"
test_endpoint "GET" "/api/games" "" "$TOKEN" "GET Game History"
test_endpoint "POST" "/api/games" '{"result":"win","userColor":"w","totalMoves":42,"openingName":"Sicilian Defense","timeControl":"10+0","ratingChange":12,"durationSeconds":1080}' "$TOKEN" "POST Save Game"
test_endpoint "GET" "/api/games" "" "$TOKEN" "GET Game History (after save)"
echo ""

# Performance Summary
echo "=========================================="
echo "Performance Summary"
echo "=========================================="
echo ""

if [ ${#RESPONSE_TIMES[@]} -gt 0 ]; then
    # Calculate statistics
    total=0
    min=999999
    max=0
    count=${#RESPONSE_TIMES[@]}
    
    for time in "${RESPONSE_TIMES[@]}"; do
        total=$(echo "$total + $time" | bc -l)
        if (( $(echo "$time < $min" | bc -l) )); then
            min=$time
        fi
        if (( $(echo "$time > $max" | bc -l) )); then
            max=$time
        fi
    done
    
    avg=$(echo "scale=2; $total / $count" | bc -l)
    
    echo -e "${BLUE}Overall Performance Statistics:${NC}"
    echo -e "  Total Requests:    ${CYAN}$count${NC}"
    echo -e "  Average Response:  ${YELLOW}${avg}ms${NC}"
    echo -e "  Fastest Request:  ${GREEN}${min}ms${NC}"
    echo -e "  Slowest Request:  ${RED}${max}ms${NC}"
    echo ""
    
    echo -e "${BLUE}Detailed Performance by Endpoint:${NC}"
    echo ""
    printf "%-40s %-10s %-12s %-12s %-12s %-12s\n" "Endpoint" "Status" "Total (ms)" "DNS (ms)" "Connect (ms)" "Transfer (ms)"
    echo "------------------------------------------------------------------------------------------------------------------------"
    
    for i in "${!ENDPOINT_NAMES[@]}"; do
        name="${ENDPOINT_NAMES[$i]}"
        code="${HTTP_CODES[$i]}"
        total_time="${RESPONSE_TIMES[$i]}"
        dns_time="${DNS_TIMES[$i]}"
        connect_time="${CONNECT_TIMES[$i]}"
        transfer_time="${TRANSFER_TIMES[$i]}"
        
        status_color=$GREEN
        if [ "$code" -ge 400 ]; then
            status_color=$RED
        fi
        
        perf_color=$(get_perf_color "$total_time")
        
        printf "%-40s ${status_color}%-10s${NC} ${perf_color}%-12s${NC} %-12s %-12s %-12s\n" \
            "${name:0:38}" "$code" "$total_time" "$dns_time" "$connect_time" "$transfer_time"
    done
    echo ""
fi

# Test Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi

