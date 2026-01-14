# CC-07: Segmentation & List Builder

## Overview
Dynamic contact segmentation with complex filters.

## Priority
P1 - Required for campaigns

## Key Features
- Dynamic lists (auto-update as contacts match)
- Static lists (manual membership)
- Complex filter builder (AND/OR/NOT)
- Filter by: tags, fields, behaviors, dates
- Segment size estimation
- Export segments to CSV

## Filter Types
- Tag contains/not contains
- Field equals/not equals/contains
- Date before/after/between
- Behavior: opened email, clicked, replied
- Source: where contact came from
- Workflow: enrolled/completed

## API Endpoints
```
POST /api/v1/segments
GET  /api/v1/segments
GET  /api/v1/segments/{id}
GET  /api/v1/segments/{id}/contacts
GET  /api/v1/segments/{id}/count
POST /api/v1/segments/{id}/export
```

## Success Criteria
- [ ] Create dynamic segments
- [ ] Complex filter builder
- [ ] Real-time count estimation
- [ ] Contact list preview
- [ ] CSV export
- [ ] Integration with campaigns
