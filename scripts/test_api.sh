#!/bin/bash

# Code-Monitor API Integration Test Script
# Usage: ./scripts/test_api.sh

set -e  # Exit on error

API_URL="http://localhost:8000"
WEEK_START="2025-10-13"  # Monday

echo "🧪 Code-Monitor API Integration Test Suite"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_api() {
    local test_name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="$4"

    echo -e "\n${YELLOW}Testing:${NC} $test_name"

    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $http_code)"
        echo "$body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Pre-flight check
echo -e "\n${YELLOW}🔍 Pre-flight checks...${NC}"

# Check if API is running
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ API is not running at $API_URL${NC}"
    echo "Please start the API first:"
    echo "  cd backend && uvicorn app.main:app --reload"
    exit 1
fi

echo -e "${GREEN}✅ API is running${NC}"

# Test 1: Health Check
test_api "Health Check" "/health"

# Test 2: Create User 1
USER1_DATA='{
    "name": "김철수",
    "email": "test1@lab.com",
    "github_username": "chulsu",
    "repo_url": "https://github.com/chulsu/repo",
    "role": "student"
}'
test_api "Create User 1" "/api/users" "POST" "$USER1_DATA"
USER1_ID=$(echo "$body" | jq -r '.id')

# Test 3: Create User 2
USER2_DATA='{
    "name": "이영희",
    "email": "test2@lab.com",
    "github_username": "younghee",
    "repo_url": "https://github.com/younghee/repo",
    "role": "student"
}'
test_api "Create User 2" "/api/users" "POST" "$USER2_DATA"
USER2_ID=$(echo "$body" | jq -r '.id')

# Test 4: List Users
test_api "List All Users" "/api/users"

# Test 5: Get Specific User
test_api "Get User 1" "/api/users/$USER1_ID"

# Test 6: Create Weekly Submission for User 1
SUBMISSION1_DATA="{
    \"week_start_date\": \"$WEEK_START\",
    \"code_lines_added\": 500,
    \"documents_created\": 3,
    \"notes\": \"Implemented authentication system\"
}"
test_api "Create Submission (User 1)" "/api/users/$USER1_ID/submissions" "POST" "$SUBMISSION1_DATA"

# Test 7: Create Weekly Submission for User 2
SUBMISSION2_DATA="{
    \"week_start_date\": \"$WEEK_START\",
    \"code_lines_added\": 800,
    \"documents_created\": 5,
    \"notes\": \"Built dashboard and API endpoints\"
}"
test_api "Create Submission (User 2)" "/api/users/$USER2_ID/submissions" "POST" "$SUBMISSION2_DATA"

# Test 8: Get User Submissions
test_api "Get User 1 Submissions" "/api/users/$USER1_ID/submissions"

# Test 9: Get All Submissions
test_api "Get All Submissions" "/api/submissions"

# Test 10: Get Current Week Submissions
test_api "Get Current Week Submissions" "/api/submissions/current-week"

# Test 11: Update Rankings for the week
test_api "Update Rankings" "/api/rankings/update/$WEEK_START" "POST"

# Test 12: Get Current Week Rankings
test_api "Get Current Week Rankings" "/api/rankings/current"

# Test 13: Get Specific Week Rankings
test_api "Get Specific Week Rankings" "/api/rankings/week/$WEEK_START"

# Test 14: Get Top 3 Performers
test_api "Get Top 3 Performers" "/api/rankings/top/3?week_start_date=$WEEK_START"

# Test 15: Get User 1 Ranking History
test_api "Get User 1 Ranking History" "/api/users/$USER1_ID/ranking/history?weeks=4"

# Summary
echo -e "\n=========================================="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo -e "=========================================="

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
