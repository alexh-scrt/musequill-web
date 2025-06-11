#!/bin/bash
# MuseQuill Newsletter Service - Curl Test Examples
# Test the /signup endpoint with various scenarios

# Base URL for the newsletter service
BASE_URL="http://localhost:8044"

echo "🖋️ MuseQuill Newsletter API Test Suite"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Basic Signup
echo -e "\n${BLUE}📧 Test 1: Basic Newsletter Signup${NC}"
echo "curl -X POST $BASE_URL/signup \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"email\": \"test@example.com\"}'"
echo ""
echo "Response:"
curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' \
  2>/dev/null | jq . 2>/dev/null || curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test 2: Comprehensive Signup with All Fields
echo -e "\n${BLUE}📧 Test 2: Comprehensive Signup with All Fields${NC}"
echo "curl -X POST $BASE_URL/signup \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{
    \"email\": \"john.doe@musequill.ink\",
    \"name\": \"John Doe\",
    \"source\": \"landing_page\",
    \"campaign\": \"early_access_2025\",
    \"interests\": [\"ai\", \"writing\", \"books\"],
    \"referrer\": \"https://google.com\",
    \"utm_source\": \"google\",
    \"utm_medium\": \"organic\",
    \"utm_campaign\": \"early_access_2025\",
    \"utm_content\": \"hero_button\"
  }'"
echo ""
echo "Response:"
curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@musequill.ink",
    "name": "John Doe", 
    "source": "landing_page",
    "campaign": "early_access_2025",
    "interests": ["ai", "writing", "books"],
    "referrer": "https://google.com",
    "utm_source": "google",
    "utm_medium": "organic", 
    "utm_campaign": "early_access_2025",
    "utm_content": "hero_button"
  }' \
  2>/dev/null | jq . 2>/dev/null || curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@musequill.ink",
    "name": "John Doe",
    "source": "landing_page", 
    "campaign": "early_access_2025",
    "interests": ["ai", "writing", "books"],
    "referrer": "https://google.com",
    "utm_source": "google",
    "utm_medium": "organic",
    "utm_campaign": "early_access_2025", 
    "utm_content": "hero_button"
  }'

# Test 3: Social Media Signup
echo -e "\n${BLUE}📧 Test 3: Social Media Signup${NC}"
echo "curl -X POST $BASE_URL/signup \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{
    \"email\": \"social.user@gmail.com\",
    \"name\": \"Social User\",
    \"source\": \"twitter\", 
    \"campaign\": \"early_access_2025\",
    \"utm_source\": \"twitter\",
    \"utm_medium\": \"social\",
    \"utm_campaign\": \"launch_announcement\"
  }'"
echo ""
echo "Response:"
curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "social.user@gmail.com",
    "name": "Social User",
    "source": "twitter",
    "campaign": "early_access_2025", 
    "utm_source": "twitter",
    "utm_medium": "social",
    "utm_campaign": "launch_announcement"
  }' \
  2>/dev/null | jq . 2>/dev/null || curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "social.user@gmail.com",
    "name": "Social User",
    "source": "twitter",
    "campaign": "early_access_2025",
    "utm_source": "twitter", 
    "utm_medium": "social",
    "utm_campaign": "launch_announcement"
  }'

# Test 4: Duplicate Email Test
echo -e "\n${BLUE}📧 Test 4: Duplicate Email Test${NC}"
echo "curl -X POST $BASE_URL/signup \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"email\": \"test@example.com\"}'"
echo ""
echo "Response (should handle duplicate gracefully):"
curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' \
  2>/dev/null | jq . 2>/dev/null || curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test 5: Invalid Email Test
echo -e "\n${BLUE}📧 Test 5: Invalid Email Test${NC}"
echo "curl -X POST $BASE_URL/signup \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"email\": \"invalid-email\"}'"
echo ""
echo "Response (should return validation error):"
curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email"}' \
  2>/dev/null | jq . 2>/dev/null || curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email"}'

# Test 6: Missing Required Field Test  
echo -e "\n${BLUE}📧 Test 6: Missing Required Field Test${NC}"
echo "curl -X POST $BASE_URL/signup \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"name\": \"No Email User\"}'"
echo ""
echo "Response (should return validation error):"
curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"name": "No Email User"}' \
  2>/dev/null | jq . 2>/dev/null || curl -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"name": "No Email User"}'

# Test 7: Bulk Signup Test (Multiple Users)
echo -e "\n${BLUE}📧 Test 7: Bulk Signup Test${NC}"
echo "Testing multiple signups in sequence..."

emails=(
  "writer1@musequill.ink"
  "author2@musequill.ink" 
  "blogger3@musequill.ink"
  "novelist4@musequill.ink"
  "journalist5@musequill.ink"
)

for i in "${!emails[@]}"; do
  email="${emails[$i]}"
  echo "Signing up: $email"
  curl -X POST "$BASE_URL/signup" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"$email\",
      \"name\": \"Test User $((i+1))\",
      \"source\": \"bulk_test\",
      \"campaign\": \"early_access_2025\"
    }" \
    -s | jq '.message' 2>/dev/null || echo "Signup attempted"
done

# Health Check
echo -e "\n${BLUE}🏥 Health Check${NC}"
echo "curl $BASE_URL/health"
echo ""
echo "Response:"
curl "$BASE_URL/health" 2>/dev/null | jq . 2>/dev/null || curl "$BASE_URL/health"

# Public Stats Check
echo -e "\n${BLUE}📊 Public Stats${NC}"
echo "curl $BASE_URL/stats"
echo ""
echo "Response:"
curl "$BASE_URL/stats" 2>/dev/null | jq . 2>/dev/null || curl "$BASE_URL/stats"

# Admin Analytics (if you have admin token)
echo -e "\n${BLUE}🔐 Admin Analytics (requires token)${NC}"
echo "curl \"$BASE_URL/analytics?token=your-admin-token\""
echo ""
echo "Note: Replace 'your-admin-token' with actual admin token from .env file"

echo -e "\n${GREEN}✅ Newsletter API Testing Complete!${NC}"
echo ""
echo "Summary of endpoints tested:"
echo "  POST /signup          - Newsletter signup"
echo "  GET  /health          - Service health check"
echo "  GET  /stats           - Public statistics"
echo "  GET  /analytics       - Admin analytics (requires token)"
echo ""
echo "Next steps:"
echo "  1. Check the database: sqlite3 data/newsletter.db 'SELECT * FROM subscribers;'"
echo "  2. View admin dashboard: http://localhost:8080/admin?token=your-admin-token"
echo "  3. Check logs: ./startup.sh logs"

# One-liner examples for quick testing
echo -e "\n${YELLOW}🚀 Quick Test Commands:${NC}"
echo ""
echo "# Basic signup test:"
echo "curl -X POST http://localhost:8080/signup -H \"Content-Type: application/json\" -d '{\"email\": \"quick.test@example.com\"}'"
echo ""
echo "# Health check:"
echo "curl http://localhost:8080/health"
echo ""
echo "# Public stats:"
echo "curl http://localhost:8080/stats"
echo ""
echo "# Check database:"
echo "sqlite3 data/newsletter.db 'SELECT email, name, source, created_at FROM subscribers ORDER BY created_at DESC LIMIT 10;'"