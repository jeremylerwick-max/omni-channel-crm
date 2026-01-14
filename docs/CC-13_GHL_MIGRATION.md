# CC-13: GHL Migration Tool
## Claude Code Task Specification

**Module:** GoHighLevel Data Migration
**Priority:** P1 (V1.0)
**Estimated Time:** 2-3 days
**Dependencies:** CRM Core

---

## Objective

One-click migration from GoHighLevel to capture market share. Import contacts, tags, conversations, pipelines.

---

## Directory Structure
```
backend/modules/migration/
├── __init__.py
├── ghl/
│   ├── client.py        # GHL API client
│   ├── importer.py      # Data import logic
│   └── mapper.py        # Field mapping
├── hubspot/
│   ├── client.py
│   └── importer.py
├── csv_import.py        # Enhanced CSV import
├── progress.py          # Progress tracking
└── tests/
```

---

## GHL API Endpoints Used
```
GET /contacts/?locationId={id}
GET /contacts/{id}/tasks
GET /contacts/{id}/notes
GET /conversations/search?locationId={id}
GET /opportunities/search?location_id={id}
GET /pipelines/?locationId={id}
GET /custom-fields/
GET /tags/
```

---

## Migration Flow

```
1. User provides GHL API key + Location ID
2. Validate credentials (test API call)
3. Preview: Show counts
   - X contacts
   - Y tags
   - Z conversations
   - N pipeline stages
4. User confirms
5. Background job imports in batches (100/batch)
6. Progress via WebSocket
7. Completion report with any errors
```

---

## API Endpoints
```
POST   /api/migration/ghl/connect         # Validate credentials
GET    /api/migration/ghl/preview         # Get counts
POST   /api/migration/ghl/start           # Begin migration
GET    /api/migration/ghl/status          # Check progress
POST   /api/migration/hubspot/connect     # HubSpot variant
POST   /api/migration/csv/upload          # CSV import
GET    /api/migration/csv/map             # Get field mapping UI
POST   /api/migration/csv/start           # Start CSV import
```

---

## Acceptance Criteria

1. ✅ Connect to GHL API
2. ✅ Import contacts with custom fields
3. ✅ Import tags
4. ✅ Import conversations (SMS history)
5. ✅ Import pipelines and opportunities
6. ✅ Progress tracking
7. ✅ Error handling (skip bad records)
8. ✅ Duplicate detection
9. ✅ CSV import with field mapping UI
10. ✅ 80%+ test coverage
