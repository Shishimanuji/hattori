# PRMS Specification - Quick Reference Guide

## 📊 Specification Overview

| Metric | Value |
|--------|-------|
| **Total Requirements** | 24 (up from 20) |
| **Implementation Phases** | 41 (up from 31) |
| **Task Waves** | 45+ |
| **Core Subtasks** | 150+ |
| **Estimated Dev-Days** | ~185 (with enhancements) |
| **Technology Stack** | React/TypeScript + FastAPI + PostgreSQL |
| **Database Tables** | 15 (up from 8) |

---

## 🎯 Requirements by Category

### Functional Requirements (19)

**Dashboard & Visualization (2)**
- Req 1: Dashboard - Project Overview
- Req 2: Dashboard - Resource Allocation Visualization

**Authentication & Authorization (2)**
- Req 3: Authentication and Authorization
- Req 20: Session Management

**User Management (1)**
- Req 4: User Management

**Project & Resource Management (4)**
- Req 5: Project CRUD Operations
- Req 6: Resource CRUD Operations
- Req 7: Asset Type Management and Dynamic Schema Discovery
- Req 8: Custom Field Validation

**Data Import & Export (2)**
- Req 9: Excel Import Functionality
- Req 17: Reporting and Export (CSV, PDF)

**Budget Management (1)**
- Req 10: Resource Allocation and Budget Tracking

**System Integration (1)**
- Req 12: REST API for System Integration

**Notifications (1)** ✨ NEW
- Req 21: Notification System

**AI/Analytics (1)** ✨ NEW
- Req 22: AI-Powered Insights and Natural Language Queries

**Advanced Reporting (1)** ✨ NEW
- Req 23: Advanced Reporting and Report Generation Engine

### Non-Functional Requirements (5)

**Data & Performance (3)**
- Req 11: Data Persistence and PostgreSQL Integration
- Req 13: Performance and Scalability
- Req 24: Dynamic Custom Field Optimization with JSONB ✨ NEW

**Security (2)**
- Req 14: Security and Data Protection
- Req 19: Enhanced Audit Logging and Compliance ✨ ENHANCED

**UX & Error Handling (2)**
- Req 15: Error Handling and Validation
- Req 16: User Interface and User Experience

---

## 🏗️ Database Schema

### Core Tables (Original)
```
1. users - Authentication & roles
2. projects - Project container
3. resources - Asset assignments (with JSONB custom fields)
4. asset_types - Resource type definitions
5. custom_fields - Schema metadata
6. allocations - Budget tracking
7. audit_logs - Change history (ENHANCED)
8. sessions - Token management
```

### New Tables
```
9. notifications - User alerts & events
10. report_templates - Report definitions with versioning
11. generated_reports - Report artifacts
12. embedding_cache - AI embeddings for RAG
```

### Updates
```
- resources.custom_field_values: TEXT → JSONB
- custom_fields.options: TEXT → JSONB
- custom_fields.validation_rules: TEXT → JSONB
- audit_logs: Extended operations (LOGIN, LOGOUT, IMPORT, EXPORT, etc.)
```

### Indexes
```
- GIN indexes on resources.custom_field_values (for JSONB queries)
- Composite indexes on frequently filtered columns
- Full-text search indexes on notifications
```

---

## 🔐 Security & Compliance

### Audit Operations Tracked
```
✅ CREATE - Resource/Project created
✅ UPDATE - Entity modified
✅ DELETE - Soft delete performed
✅ LOGIN - User authenticated
✅ LOGOUT - Session ended
✅ IMPORT - Excel import executed
✅ EXPORT - Data exported
✅ REPORT_DOWNLOAD - Report accessed
✅ ROLE_CHANGE - User role modified
```

### Compliance Features
- **24-month audit retention** (government compliance)
- **Encryption at-rest** for sensitive audit data
- **Immutable audit logs** (cannot be modified)
- **Admin-only access** to audit logs
- **Compliance reporting** by date range, user, operation type

---

## 🔔 Notification System

### Trigger Events
```
Budget Threshold Reached (80%, 100%)
  ↓ Creates: BUDGET_THRESHOLD_{80,100} notification
  ↓ Recipients: Project manager, Admins
  ↓ Channels: In-app + Email

Warranty Expiring (≤30 days)
  ↓ Creates: WARRANTY_EXPIRING notification
  ↓ Recipients: Custodian, Asset manager
  ↓ Channels: In-app

Import Failed/Completed
  ↓ Creates: IMPORT_FAILED / IMPORT_COMPLETED notification
  ↓ Recipients: Import initiator
  ↓ Channels: In-app + Email (if failed)

Project Delayed
  ↓ Creates: PROJECT_DELAYED notification
  ↓ Recipients: Project manager
  ↓ Channels: In-app + Email
```

### User Controls
- Mark notifications as read/dismissed
- Configure per-type preferences (in-app, email, frequency)
- View notification history
- Manage notification center

---

## 🤖 AI/NLQ Service Layer

### Natural Language Query Flow
```
User Input: "Show overbudget projects"
         ↓
LLM SQL Agent:
  - Parse intent
  - Generate SELECT-only SQL
  - Validate safety
         ↓
JSONB Query:
  SELECT * FROM projects 
  WHERE allocated_budget > budget
         ↓
RAG Pipeline:
  - Search similar queries
  - Find related patterns
  - Embed results
         ↓
Response:
  - Structured JSON results
  - AI insights + recommendations
  - Related suggestions
```

### Components
```
services/ai/
├── sql_agent.py - NLQ to SQL translation
├── rag_agent.py - Retrieval-augmented generation
├── report_agent.py - Insights & forecasting
└── embeddings.py - Vector embeddings
```

### Safety Guarantees
✅ Only SELECT queries (no INSERT/UPDATE/DELETE)
✅ Sensitive data filtering from results
✅ Query timeouts and error handling
✅ All queries logged for audit
✅ Graceful LLM service fallback

---

## 📄 Advanced Reporting Engine

### Report Templates
```
Available Templates:
1. Project Budget Analysis
2. Resource Utilization Report
3. Warranty Status Report
4. Team Performance Summary
5. Custom user-defined templates

Template Sections:
- Summary (AI-generated narrative)
- Tables (query results)
- Charts (visualizations)
- Recommendations (AI insights)
```

### Supported Formats
```
PDF   - Charts as images, headers/footers, company branding
XLSX  - Multiple sheets (summary, details, charts)
DOCX  - Formatted sections, embedded charts
CSV   - Flat data for analysis
HTML  - Web-viewable, interactive
```

### Scheduling
```
Daily/Weekly/Monthly Reports
↓
Auto-generate on schedule
↓
Email to recipients
↓
Store in generated_reports table
```

### Template Versioning
```
V1 → Initial template
V2 → Added metric
V3 → Changed visualization
...
Reports track which version was used
```

---

## ⚡ JSONB Optimization

### Before (TEXT)
```sql
custom_field_values TEXT
WHERE custom_field_values LIKE '%department:IT%'
→ Full table scan
→ 2500ms for 1M rows
❌ Expensive
```

### After (JSONB)
```sql
custom_field_values JSONB
WHERE custom_field_values @> '{"department": "IT"}'
CREATE INDEX USING GIN on custom_field_values
→ Index scan via GIN
→ 10ms for 1M rows
✅ 250x faster!
```

### Query Operators
```
@>     - Contains: '{"dept": "IT"}'
->     - Extract JSON: custom_fields->'name'
->>    - Extract text: custom_fields->>'department'
?      - Has key: custom_fields ? 'location'
```

---

## 📋 Implementation Phases

### Wave Groups

**Phase 1-2:** Setup (Backend, Frontend, Database)
**Phase 3-5:** Auth & Users
**Phase 6-9:** Projects & Assets
**Phase 10-16:** RBAC & Dashboard [Checkpoint 1]
**Phase 17-20:** Imports & Logging
**Phase 21-25:** Error Handling [Checkpoint 2]
**Phase 26-30:** Security & API
**Phase 31-34:** Audit Logging & Notifications & JSONB ✨ NEW
**Phase 35-36:** Reporting Engine ✨ NEW
**Phase 37-39:** AI/NLQ Service ✨ NEW
**Phase 40-41:** Enterprise Checkpoint & Final ✨ NEW

### Critical Dependencies
```
Database Schema (Phase 3)
  ↓
API Layer (Phase 4)
  ↓
Dashboard Backend (Phase 14)
  ↓
JSONB Optimization (Phase 34) - Can run in parallel
  ↓
Notification System (Phase 32)
  ↓
Reporting Engine (Phase 35)
  ↓
AI/NLQ Service (Phase 37)
```

---

## 📊 Performance Targets

### Response Times
```
Dashboard Load:         < 2 seconds (1,000 resources)
Search/Filter:          < 1 second (100,000 records)
JSONB Custom Queries:   < 1 second (1M records with GIN index)
Excel Import:           < 30 seconds (10,000 records)
Chart Refresh:          < 1 second (no page reload)
Export Generation:      < 30 seconds (10,000 records)
API Response:           < 500ms (typical query)
```

### Scalability
```
Concurrent Users:       100+ simultaneous connections
Records per table:      10M+ rows supported
Custom fields:          Up to 20 per asset type
Audit log retention:    24 months (~100M records)
Session tokens:         No practical limit
Report templates:       Unlimited (with versioning)
```

---

## 🎨 UI Components

### New Components (Enhancements)
```
Notifications:
  - Toast component
  - Notification center
  - Badge with count
  - Preferences modal

Reporting:
  - Template selector
  - Parameter form
  - Progress indicator
  - Report download manager
  - Schedule manager

AI/NLQ:
  - Query input
  - Results table
  - Insights panel
  - Query history
  - Template library
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All 24 requirements implemented
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All property-based tests passing (24 properties)
- [ ] Performance tests verified
- [ ] Security penetration testing complete
- [ ] Database migrations tested on staging
- [ ] Load testing (100+ concurrent users)

### Deployment Steps
1. **Database**: Run migration scripts (add JSONB, new tables)
2. **Backend**: Deploy API layer with new services
3. **Frontend**: Deploy React bundle
4. **LLM**: Configure LLM service endpoint
5. **Email**: Configure SMTP for notifications
6. **Storage**: Configure S3/filesystem for reports
7. **Extensions**: Enable pgvector in PostgreSQL

### Post-Deployment
- [ ] Verify all endpoints responding
- [ ] Check audit logging
- [ ] Verify notifications triggering
- [ ] Test AI/NLQ service
- [ ] Generate test report
- [ ] Monitor error logs
- [ ] Verify performance baselines

---

## 📞 Key Contacts & Resources

### Files in This Spec
```
requirements.md - 24 requirements with acceptance criteria
design.md - Architecture, schemas, components, properties
tasks.md - 41 implementation phases with 150+ subtasks
ENHANCEMENTS.md - Detailed explanation of new features
QUICK_REFERENCE.md - This file
```

### Tech Stack Decision
```
Frontend: React + TypeScript + Vite + Tailwind + ShadCN + ECharts
Backend: FastAPI + SQLAlchemy + Pydantic
Database: PostgreSQL with pgvector extension
AI: OpenAI GPT-4 or self-hosted LLM
Email: SMTP or SendGrid
Storage: S3 or local filesystem
```

---

## ❓ FAQ

**Q: Can I skip AI/NLQ and focus on core features?**
A: Yes! Phases 1-30 are complete core features. Phases 37-39 (AI) are optional enhancements.

**Q: How long to implement?**
A: Core only (~80 days), with all enhancements (~185 days for 2-3 developers).

**Q: Is JSONB migration risky?**
A: No - it's done as a non-breaking change with parallel columns and gradual cutover.

**Q: What if LLM service goes down?**
A: System gracefully degrades - natural language queries fail gracefully, rest of system unaffected.

**Q: Can I deploy phase by phase?**
A: Yes - checkpoints at phases 16, 25, and 40 allow staged rollout.

**Q: How do I handle government audits?**
A: Use enhanced audit logs (Req 19) to export compliance reports with full change history.

---

## 🎓 Learning Path

### Week 1-2: Setup & Infrastructure
- Phase 1-2: Backend and frontend scaffolding
- Phase 3: Database schema
- Checkpoint: Both stacks running locally

### Week 3-4: Auth & Core CRUD
- Phase 4-5: Authentication
- Phase 6-9: Projects and resources
- Checkpoint: Can create/edit projects

### Week 5-6: Dashboard
- Phase 14-16: Dashboard metrics and UI
- Checkpoint 1: Dashboard working, basic CRUD complete

### Week 7-8: Advanced Features
- Phase 17-20: Import, logging, exports
- Phase 21-25: Error handling, security
- Checkpoint 2: All core features working

### Week 9-10: Enterprise Features
- Phase 31-34: Audit logging, notifications, JSONB
- Phase 35-36: Reporting engine
- Checkpoint 3: Enterprise features working

### Week 11-12: AI & Final
- Phase 37-39: AI/NLQ service
- Phase 40-41: Final testing and deployment
- Production ready!

---

**Last Updated:** 2024  
**Specification Version:** 2.0 (with Enterprise Enhancements)  
**Status:** Ready for Implementation 🚀
