# Module Specs Overview

This directory contains detailed specifications for each development module. Each module is designed to be built **independently** by a separate Claude Code instance.

## Execution Strategy

### Wave 1 (Week 1) - Foundation
| Module | Spec File | Priority | Dependencies |
|--------|-----------|----------|--------------|
| CC-01 | [EMAIL_SERVICE.md](./CC-01_EMAIL_SERVICE.md) | P0 | None |
| CC-02 | [VOICE_SERVICE.md](./CC-02_VOICE_SERVICE.md) | P1 | None |
| CC-03 | [WORKFLOW_ENGINE.md](./CC-03_WORKFLOW_ENGINE.md) | P0 | None |
| CC-04 | [API_EXPANSION.md](./CC-04_API_EXPANSION.md) | P1 | None |

### Wave 2 (Week 2) - Core Features
| Module | Spec File | Priority | Dependencies |
|--------|-----------|----------|--------------|
| CC-05 | [VISUAL_BUILDER.md](./CC-05_VISUAL_BUILDER.md) | P0 | CC-03 |
| CC-06 | [AI_TESTING.md](./CC-06_AI_TESTING.md) | P0 | CC-03 |
| CC-07 | [SEGMENTATION.md](./CC-07_SEGMENTATION.md) | P1 | None |
| CC-08 | [PIPELINES.md](./CC-08_PIPELINES.md) | P2 | None |
| CC-09 | [BILLING.md](./CC-09_BILLING.md) | P1 | None |

### Wave 3 (Week 3) - Polish
| Module | Spec File | Priority | Dependencies |
|--------|-----------|----------|--------------|
| CC-10 | [WHITE_LABEL.md](./CC-10_WHITE_LABEL.md) | P3 | CC-09 |
| CC-11 | [ANALYTICS.md](./CC-11_ANALYTICS.md) | P2 | None |
| CC-12 | [RBAC.md](./CC-12_RBAC.md) | P2 | None |
| CC-13 | [MIGRATION.md](./CC-13_MIGRATION.md) | P2 | None |
| CC-14 | [10DLC.md](./CC-14_10DLC.md) | P2 | CC-02 |
| CC-15 | [FRONTEND_UI.md](./CC-15_FRONTEND_UI.md) | P0 | All backend |

## How to Use

1. Open a Claude Code instance
2. Copy the relevant spec file into the task
3. Point it to the repo: `/Users/mac/Desktop/omni-channel-crm`
4. Let it build

## Integration Points

All modules integrate via:
- **Database:** PostgreSQL with SQLAlchemy models
- **API:** FastAPI routes at `/api/v1/`
- **Events:** Redis pub/sub for real-time
- **Queue:** Redis for background jobs

## Module Communication

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Frontend   │◄──►│   API Layer  │◄──►│   Services   │
│   (CC-15)    │    │   (CC-04)    │    │  (CC-01-03)  │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌──────────────┐ ┌──────────────┐
            │  PostgreSQL  │ │    Redis     │
            │  (all data)  │ │ (queue/pub)  │
            └──────────────┘ └──────────────┘
```
