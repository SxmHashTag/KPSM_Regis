# Diamond Forensics API Documentation

## Overview
The Diamond Forensics Management System provides a RESTful API for managing forensic cases, evidence, persons, documents, and related data.

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
All API endpoints (except the root) require authentication. The API supports:
- **Session Authentication** - For browser-based access
- **Basic Authentication** - For programmatic access

### Login
To access the browsable API in a browser:
1. Navigate to `http://127.0.0.1:8000/api-auth/login/`
2. Login with your Django user credentials

## Available Endpoints

### Cases
- **List/Create Cases**: `GET/POST /api/cases/`
- **Retrieve/Update/Delete Case**: `GET/PUT/PATCH/DELETE /api/cases/{id}/`
- **Get Case Evidence**: `GET /api/cases/{id}/evidence/`
- **Get Case Persons**: `GET /api/cases/{id}/persons/`
- **Get Case Tasks**: `GET /api/cases/{id}/tasks/`

**Filters**: `status`, `priority`, `case_type`, `department`
**Search**: `case_number`, `case_name`, `description`, `prosecutor`
**Ordering**: `date_opened`, `date_closed`, `created_at`, `case_number`

### Persons
- **List/Create Persons**: `GET/POST /api/persons/`
- **Retrieve/Update/Delete Person**: `GET/PUT/PATCH/DELETE /api/persons/{id}/`

**Filters**: `person_type`, `city`, `state`, `country`
**Search**: `first_name`, `last_name`, `middle_name`, `email`, `ssn`
**Ordering**: `last_name`, `first_name`, `created_at`

### Evidence
- **List/Create Evidence**: `GET/POST /api/evidence/`
- **Retrieve/Update/Delete Evidence**: `GET/PUT/PATCH/DELETE /api/evidence/{id}/`
- **Get Evidence Transfers**: `GET /api/evidence/{id}/transfers/`
- **Get Evidence Images**: `GET /api/evidence/{id}/images/`

**Filters**: `case`, `device_type`, `status`, `state`, `current_department`, `damages`
**Search**: `evidence_number`, `ibs_number`, `item_name`, `description`, `serial_number`, `imei`, `brand`, `model`
**Ordering**: `collected_date`, `created_at`, `evidence_number`

### Evidence Transfers (Chain of Custody)
- **List/Create Transfers**: `GET/POST /api/evidence-transfers/`
- **Retrieve/Update/Delete Transfer**: `GET/PUT/PATCH/DELETE /api/evidence-transfers/{id}/`

**Filters**: `evidence`, `from_department`, `to_department`
**Ordering**: `transfer_date`, `created_at`

### Evidence Images
- **List/Create Images**: `GET/POST /api/evidence-images/`
- **Retrieve/Update/Delete Image**: `GET/PUT/PATCH/DELETE /api/evidence-images/{id}/`

**Filters**: `evidence`
**Ordering**: `uploaded_at`

### Documents
- **List/Create Documents**: `GET/POST /api/documents/`
- **Retrieve/Update/Delete Document**: `GET/PUT/PATCH/DELETE /api/documents/{id}/`

**Filters**: `case`, `evidence`, `document_type`, `is_confidential`, `access_level`
**Search**: `title`, `description`, `author`, `file_name`
**Ordering**: `date_created`, `created_at`

### Tasks
- **List/Create Tasks**: `GET/POST /api/tasks/`
- **Retrieve/Update/Delete Task**: `GET/PUT/PATCH/DELETE /api/tasks/{id}/`

**Filters**: `case`, `task_type`, `status`, `priority`, `assigned_to`
**Search**: `task_name`, `description`, `assigned_to`
**Ordering**: `due_date`, `created_at`, `priority`

### Timeline Activities
- **List/Create Activities**: `GET/POST /api/timeline-activities/`
- **Retrieve/Update/Delete Activity**: `GET/PUT/PATCH/DELETE /api/timeline-activities/{id}/`

**Filters**: `case`, `activity_type`, `related_evidence`, `related_person`
**Search**: `title`, `description`, `performed_by`
**Ordering**: `activity_date`, `created_at`

### Notifications
- **List/Create Notifications**: `GET/POST /api/notifications/`
- **Retrieve/Update/Delete Notification**: `GET/PUT/PATCH/DELETE /api/notifications/{id}/`
- **Mark as Read**: `POST /api/notifications/{id}/mark_read/`

**Filters**: `case`, `notification_type`, `priority`, `is_read`
**Ordering**: `created_at`, `expires_at`

### User Profiles
- **List/Create Profiles**: `GET/POST /api/user-profiles/`
- **Retrieve/Update/Delete Profile**: `GET/PUT/PATCH/DELETE /api/user-profiles/{id}/`

**Filters**: `role`, `department`, `is_active`
**Search**: `username`, `full_name`
**Ordering**: `created_at`, `full_name`

### Access Requests
- **List/Create Requests**: `GET/POST /api/access-requests/`
- **Retrieve/Update/Delete Request**: `GET/PUT/PATCH/DELETE /api/access-requests/{id}/`
- **Approve Request**: `POST /api/access-requests/{id}/approve/`
- **Deny Request**: `POST /api/access-requests/{id}/deny/`

**Filters**: `status`, `requester`, `case`, `evidence`
**Ordering**: `created_at`, `reviewed_at`

### Case-Person Relationships
- **List/Create Relationships**: `GET/POST /api/case-persons/`
- **Retrieve/Update/Delete Relationship**: `GET/PUT/PATCH/DELETE /api/case-persons/{id}/`

**Filters**: `case`, `person`, `role`, `is_primary`
**Ordering**: `date_added`, `created_at`

## Example Requests

### Using cURL with Basic Authentication
```bash
# List all cases
curl -u username:password http://127.0.0.1:8000/api/cases/

# Get a specific case
curl -u username:password http://127.0.0.1:8000/api/cases/{case-id}/

# Create a new case
curl -u username:password -X POST \
  -H "Content-Type: application/json" \
  -d '{"case_name":"New Case","status":"active","priority":"medium"}' \
  http://127.0.0.1:8000/api/cases/

# Filter cases by status
curl -u username:password http://127.0.0.1:8000/api/cases/?status=active

# Search evidence
curl -u username:password http://127.0.0.1:8000/api/evidence/?search=iPhone
```

### Using Python requests
```python
import requests
from requests.auth import HTTPBasicAuth

# Base URL
BASE_URL = "http://127.0.0.1:8000/api"
auth = HTTPBasicAuth('username', 'password')

# List cases
response = requests.get(f"{BASE_URL}/cases/", auth=auth)
cases = response.json()

# Create evidence
evidence_data = {
    "item_name": "iPhone 12",
    "device_type": "mobile",
    "status": "collected",
    "brand": "Apple",
    "model": "iPhone 12"
}
response = requests.post(f"{BASE_URL}/evidence/", json=evidence_data, auth=auth)
new_evidence = response.json()

# Get evidence for a specific case
case_id = "some-uuid-here"
response = requests.get(f"{BASE_URL}/cases/{case_id}/evidence/", auth=auth)
evidence_list = response.json()
```

## Pagination
API responses are paginated with 50 items per page by default. Pagination information is included in the response:

```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/cases/?page=2",
  "previous": null,
  "results": [...]
}
```

Navigate pages using the `page` query parameter:
```
/api/cases/?page=2
```

## Filtering, Searching, and Ordering

### Filtering
Use query parameters to filter results:
```
/api/cases/?status=active&priority=high
/api/evidence/?device_type=mobile&status=collected
```

### Searching
Use the `search` parameter for text search:
```
/api/cases/?search=fraud
/api/persons/?search=john
```

### Ordering
Use the `ordering` parameter to sort results:
```
/api/cases/?ordering=-date_opened  # Descending
/api/evidence/?ordering=collected_date  # Ascending
```

## Browsable API
Navigate to `http://127.0.0.1:8000/api/` in your browser for an interactive, browsable API interface provided by Django REST Framework.

## Response Formats
The API returns JSON by default. You can also request different formats:
- JSON: `Accept: application/json`
- Browsable HTML: `Accept: text/html`

## Error Responses
The API returns standard HTTP status codes:
- `200 OK` - Successful GET/PUT/PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include details:
```json
{
  "detail": "Error message here",
  "field_name": ["Field-specific error"]
}
```
