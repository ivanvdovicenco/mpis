# Persona Creation Workflow Enhancement

## Overview

The `genesis_mvp_workflow.json` has been enhanced with new nodes to support persona creation with description input and Google Drive folder integration.

## New Workflow: Create Persona

### Nodes Added

1. **Create Persona Webhook** (`/create-persona`)
   - Entry point for persona creation
   - Accepts POST requests with persona details
   - Webhook ID: `create-persona`

2. **List Google Drive Folders**
   - Integrates with Google Drive API
   - Lists available folders for persona storage
   - Requires Google Drive OAuth2 credentials configured in n8n

3. **Build Persona Request**
   - Constructs the complete payload for Genesis API
   - Maps input fields and applies defaults
   - Combines persona details with Google Drive folder ID

4. **Create Persona Job**
   - Sends POST request to Genesis API (`/genesis/start`)
   - Initiates persona generation workflow

5. **Respond Create Persona**
   - Returns job response to the caller
   - Includes job_id for status tracking

### Request Format

**Endpoint:** `POST /webhook/create-persona`

**Payload:**
```json
{
  "persona_name": "Alexey",
  "description": "A persona inspired by Tim Keller's pastoral wisdom",
  "language": "ru",
  "public_persona": true,
  "public_name": "Tim Keller",
  "gdrive_folder_id": "1abc123def456",
  "notes": "Focus on pastoral wisdom and apologetics",
  "inspiration_source": "Tim Keller"
}
```

**Fields:**
- `persona_name` (required): Name for the persona
- `description` (optional): Description of the persona
- `language` (optional, default: "en"): Primary language
- `public_persona` (optional, default: false): Enable web enrichment
- `public_name` (optional): Public name to search for
- `gdrive_folder_id` (optional): Google Drive folder ID for document import
- `notes` (optional): Additional context
- `inspiration_source` (optional): Primary inspiration source

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "awaiting_approval",
  "draft_no": 1,
  "human_prompt": "Review the generated persona...",
  "preview": {
    "persona_id": null,
    "name": "Alexey",
    "slug": "alexey",
    "active_version": "draft",
    "summary": "...",
    "top_topics": ["..."],
    "dominant_tones": ["..."],
    "next_actions": ["..."]
  }
}
```

## Workflow Integration

The new persona creation flow is seamlessly integrated alongside the existing Genesis workflows:

### Flow Chain
```
Create Persona Webhook 
  → List Google Drive Folders 
    → Build Persona Request 
      → Create Persona Job 
        → Respond Create Persona
```

### Data Flow
1. User sends persona details via webhook
2. Workflow lists available Google Drive folders
3. Request builder combines all inputs:
   - Persona details from webhook
   - Google Drive folder ID (if provided)
   - Default values for optional fields
4. HTTP request sent to Genesis API
5. Response returned to caller with job_id

## Google Drive Integration

### Prerequisites
1. Configure Google Drive OAuth2 credentials in n8n:
   - Go to Settings → Credentials
   - Add new "Google Drive OAuth2 API" credential
   - Authorize with Google account
   - Set credential ID to "1" or update the workflow

2. The workflow uses the credential named "Google Drive Account"

### Folder Selection
- The `List Google Drive Folders` node retrieves available folders
- User can specify `gdrive_folder_id` in the webhook payload
- If provided, Genesis API will import documents from that folder

**Note on Performance:** The workflow lists Google Drive folders on every request to ensure fresh folder data. For high-volume scenarios, consider:
- Caching folder information
- Making the Google Drive step conditional based on `gdrive_folder_id` presence
- Pre-selecting folder IDs outside the workflow

## Existing Workflows Preserved

All existing workflows remain unchanged and functional:

1. **Start Genesis Webhook** → Start Genesis Job → Respond Start
2. **Approve Genesis Webhook** → Approve Genesis Job → Respond Approve  
3. **Status Genesis Webhook** → Get Genesis Status → Respond Status

## Node Positions

The workflow is laid out in a clear visual hierarchy:
- Row 1 (y=100): Create Persona workflow nodes
- Row 2 (y=300): Start Genesis workflow nodes
- Row 3 (y=500): Approve Genesis workflow nodes
- Row 4 (y=700): Status Genesis workflow nodes

## Testing

To test the new workflow:

1. Import `genesis_mvp_workflow.json` into n8n
2. Configure Google Drive credentials
3. Activate the workflow
4. Send a POST request to the create-persona webhook:

```bash
curl -X POST http://n8n-host:5678/webhook/create-persona \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Test Persona",
    "description": "A test persona",
    "language": "en",
    "gdrive_folder_id": "your-folder-id"
  }'
```

5. Check the response for job_id
6. Use the status webhook to track progress:

```bash
curl http://n8n-host:5678/webhook/genesis-status/JOB_ID
```

## Benefits

1. **User-Friendly Input**: Simplified persona creation via webhook
2. **Google Drive Integration**: Seamless document import from Drive
3. **Credential Management**: Uses n8n's secure OAuth2 credential storage
4. **Proper Data Flow**: Well-structured request building and API communication
5. **Backward Compatible**: Existing workflows remain unchanged
