# Omni-Channel CRM & Automation Platform

> **Enterprise-grade marketing automation platform that matches and exceeds GoHighLevel**

[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()
[![Phase](https://img.shields.io/badge/Phase-MVP-blue)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

## 🎯 Vision

Build the most powerful omni-channel CRM and marketing automation platform, featuring:
- **AI Workflow Testing** - LLM-powered campaign validation (industry first)
- **Code-Driven Workflows** - YAML/JSON configs with visual builder parity
- **True Omni-Channel** - SMS, Email, Voice, WhatsApp in unified campaigns
- **Enterprise Scale** - 1M+ contacts, 10M+ events/month
- **White-Label SaaS** - Full agency reselling capability

## 📋 Documentation

| Document | Description |
|----------|-------------|
| [PRD_MAIN.md](./PRD_MAIN.md) | Core product requirements |
| [PRD_ADDENDUM.md](./PRD_ADDENDUM_MISSING_REQUIREMENTS.md) | Billing, White-Label, Migration specs |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Technical architecture (coming) |
| [API_SPEC.md](./API_SPEC.md) | API documentation (coming) |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  Dashboard │ Workflow Builder │ Contacts │ Analytics │ Admin │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                      API GATEWAY                             │
│              FastAPI + Authentication + Rate Limiting        │
└─────────────────────────┬───────────────────────────────────┘
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
┌────┴────┐         ┌────┴────┐         ┌────┴────┐
│ Workflow │         │   CRM   │         │ Comms   │
│  Engine  │         │ Service │         │ Service │
└────┬────┘         └────┬────┘         └────┬────┘
     │                    │                    │
     │              ┌─────┴─────┐        ┌────┴────┐
     │              │ PostgreSQL │        │ Twilio  │
     │              └───────────┘        │ SendGrid│
     │                                   └─────────┘
     │
┌────┴────────────────────────────────────────────┐
│              AI TESTING LAYER                    │
│  OpenAI │ Anthropic │ Ollama │ Custom LLM       │
└─────────────────────────────────────────────────┘
```

## 🚀 Modules

### MVP (4-6 weeks)
| Module | Status | Description |
|--------|--------|-------------|
| Core CRM | ✅ Built | Contacts, Tags, Conversations |
| SMS/Twilio | ✅ Built | 2-way SMS with compliance |
| AI Responses | ✅ Built | Claude Haiku auto-reply |
| Compliance | ✅ Built | DND, opt-out, quiet hours |
| NL Commands | ✅ Built | "Text John saying..." |
| Email Service | 🔄 Building | SendGrid integration |
| Voice/Calls | 🔄 Building | Twilio Voice |
| Workflow Engine v2 | 🔄 Building | YAML/JSON configs |
| Visual Builder | ⏳ Planned | React Flow canvas |
| AI Testing | ⏳ Planned | LLM workflow validation |
| Billing/Stripe | ⏳ Planned | Subscriptions + usage |
| White-Label | ⏳ Planned | Agency sub-accounts |

### V1.0 (8-10 weeks)
- Full visual workflow builder
- Complete API coverage
- Analytics dashboard
- User roles/RBAC
- GHL migration tool
- 10DLC registration wizard

### V2.0 (12-16 weeks)
- WhatsApp integration
- AI campaign optimization
- Marketplace for templates
- Advanced analytics/BI
- International expansion

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, TailwindCSS, React Flow |
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL, Redis |
| Queue | Redis (upgrading to Kafka for scale) |
| AI | OpenAI, Anthropic, Ollama |
| SMS/Voice | Twilio |
| Email | SendGrid, Resend |
| Payments | Stripe |
| Deployment | Docker, Kubernetes |
| Monitoring | Prometheus, Grafana, Jaeger |

## 📁 Repository Structure

```
omni-channel-crm/
├── docs/                    # Documentation
│   ├── PRD_MAIN.md
│   ├── PRD_ADDENDUM.md
│   └── architecture/
├── backend/                 # FastAPI services
│   ├── api/
│   ├── modules/
│   │   ├── crm/
│   │   ├── workflow/
│   │   ├── messaging/
│   │   ├── ai/
│   │   └── billing/
│   ├── workers/
│   └── tests/
├── frontend/                # React application
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── hooks/
│   └── tests/
├── infrastructure/          # Docker, K8s configs
└── scripts/                 # Automation scripts
```

## 🏃 Quick Start

```bash
# Clone the repository
git clone https://github.com/jeremylerwick-max/omni-channel-crm.git
cd omni-channel-crm

# Start infrastructure
docker-compose up -d

# Start backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload

# Start frontend
cd frontend
npm install
npm run dev
```

## 📊 Comparison with GoHighLevel

| Feature | GoHighLevel | Omni-Channel CRM |
|---------|-------------|------------------|
| SMS/MMS | ✅ | ✅ |
| Email | ✅ | ✅ |
| Voice | ✅ | ✅ |
| Visual Workflows | ✅ | ✅ |
| **Code-Driven Workflows** | ❌ | ✅ |
| **AI Workflow Testing** | ❌ | ✅ |
| **Natural Language Control** | ❌ | ✅ |
| White-Label | ✅ | ✅ |
| API | Limited | Full |
| **Local AI Option** | ❌ | ✅ |

## 👥 Team

**Ziloss Technologies**
- Jeremy Lerwick - Founder/CEO
- Claude AI Fleet - Development

## 📄 License

Proprietary - Ziloss Technologies © 2026

---

*Building the future of marketing automation*
