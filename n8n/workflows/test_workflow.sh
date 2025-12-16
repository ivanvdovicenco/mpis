#!/bin/bash
# Sample commands to test the enhanced n8n Genesis workflow

# Set your n8n host (update as needed)
N8N_HOST="${N8N_HOST:-http://localhost:5678}"

# Check if jq is available for JSON formatting
if command -v jq &> /dev/null; then
    JSON_FORMAT="jq ."
else
    JSON_FORMAT="cat"
    echo "Note: jq not found. Install jq for formatted JSON output."
    echo ""
fi

echo "Testing n8n Genesis MVP Workflow"
echo "================================="
echo ""

# Test 1: Create Persona with minimal fields
echo "Test 1: Create Persona (Minimal)"
echo "---------------------------------"
curl -X POST "${N8N_HOST}/webhook/create-persona" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Test Persona"
  }' | $JSON_FORMAT

echo ""
echo ""

# Test 2: Create Persona with description and language
echo "Test 2: Create Persona (With Description)"
echo "------------------------------------------"
curl -X POST "${N8N_HOST}/webhook/create-persona" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Alexey",
    "description": "A persona inspired by Tim Keller pastoral wisdom",
    "language": "ru",
    "notes": "Focus on apologetics and pastoral care"
  }' | $JSON_FORMAT

echo ""
echo ""

# Test 3: Create Persona with Google Drive folder
echo "Test 3: Create Persona (With Google Drive)"
echo "-------------------------------------------"
curl -X POST "${N8N_HOST}/webhook/create-persona" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Tim Keller Inspired",
    "description": "A persona based on Tim Keller teachings",
    "language": "en",
    "public_persona": true,
    "public_name": "Tim Keller",
    "gdrive_folder_id": "1abc123def456",
    "notes": "Import sermons and writings from Google Drive",
    "inspiration_source": "Tim Keller"
  }' | $JSON_FORMAT

echo ""
echo ""

# Test 4: Get Genesis Job Status
echo "Test 4: Check Job Status"
echo "------------------------"
echo "Replace JOB_ID with the job_id from previous response"
# JOB_ID="550e8400-e29b-41d4-a716-446655440000"
# curl -X GET "${N8N_HOST}/webhook/genesis-status/${JOB_ID}" | $JSON_FORMAT

echo ""
echo ""

# Test 5: Original Start Genesis endpoint (backward compatibility)
echo "Test 5: Original Start Genesis (Backward Compatible)"
echo "-----------------------------------------------------"
curl -X POST "${N8N_HOST}/webhook/genesis-start" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Original Flow Test",
    "language": "en",
    "sources": []
  }' | $JSON_FORMAT

echo ""
echo "All tests completed!"
echo ""
echo "Note: Responses will contain job_id values that can be used"
echo "      with the genesis-status endpoint to check progress."
