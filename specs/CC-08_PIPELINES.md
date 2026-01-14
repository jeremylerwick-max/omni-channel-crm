# CC-08: Pipeline & Opportunity CRM

## Overview
Sales pipeline management with drag-and-drop stages.

## Priority: P2

## Features
- Multiple pipelines
- Customizable stages
- Drag-and-drop opportunities
- Deal value tracking
- Win/loss tracking
- Pipeline analytics

## Database
```sql
CREATE TABLE pipelines (id, account_id, name, stages JSONB);
CREATE TABLE opportunities (id, pipeline_id, contact_id, stage, value, status);
```

## Success Criteria
- [ ] Create/manage pipelines
- [ ] Opportunity CRUD
- [ ] Stage management
- [ ] Value tracking
- [ ] Basic analytics
