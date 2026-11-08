# Product scope and roadmap

## Implemented in this foundation

- Responsive Oxblood Chrome workspace UI with spacious content layout.
- Live date and API/database health reporting.
- PDF/DOCX resume intake, validation, parsing and private file storage.
- Structured candidate data, candidate search/review filtering, parser warnings, source evidence and manual profile correction.
- Multi-file resume uploads with per-file progress, duplicate/error summary and parsed-candidate review.
- Role/job creation, editing, status changes and deletion.
- Application creation, duplicate protection, stage movement and notes.
- Interview scheduling, status updates, participants, notes and scorecard persistence.
- Activity log and live operational analytics.
- Hybrid transparent matching with component scores and explanations.
- Optional authentication, role checks and bootstrap administrator.
- PostgreSQL schema, initial Alembic migration, Docker Compose and backend tests.
- Supervised ranking training workflow with candidate-grouped hold-out and metrics.

## Next engineering waves

### Wave 1 — Recruiter experience

- Better manual editors for each structured profile section (beyond the JSON advanced editor).
- Candidate merge/duplicate-resolution workflow.
- Application-specific activity/history timeline with detailed before/after change diffs.
- Reusable interview templates and structured multi-interviewer consensus scorecards.
- CSV exports and scheduled reports.

### Wave 2 — Data and processing

- Background task queue for large batches and OCR workloads.
- Document malware scanning and content-disarm policy.
- Object storage adapter with private signed downloads.
- Data retention and right-to-delete workflows.
- Improved layout-aware extraction and parser evaluation corpus.
- Skill taxonomy management and alias review tools.

### Wave 3 — Collaboration and integrations

- True multi-tenant workspace isolation at the database and API query layer.
- Workspace membership and invitations.
- SSO/OIDC, password reset, session revocation and MFA.
- Email/calendar integrations and interview reminders.
- Job-board import/export connectors.
- Webhooks and documented public API keys.

### Wave 4 — ML and measurement

- Human-reviewed labels with adjudication and inter-rater agreement tracking.
- Temporal and grouped validation, segment-level error analysis and bias audits.
- Calibration and ranking metrics by job family.
- Model registry, version pinning, rollback and drift monitoring.
- Retrieval-assisted skill taxonomy and evidence-grounded explanations.
- Re-test with new job families before model promotion.

### Wave 5 — Production operations

- Centralized structured logs and error tracking.
- Metrics, tracing and service-level objectives.
- Backups and restore tests.
- Secrets manager, TLS and hardened reverse proxy.
- Load testing, dependency scanning and software bill of materials.
- Deployment environments and staged releases.

## Product principles

1. Extraction should be reviewable, with evidence and uncertainty visible.
2. Scores are decision-support signals, not deterministic hiring outcomes.
3. Missing information must be distinguished from negative evidence.
4. Recruiter workflow state must be persistent and auditable.
5. Candidate data must be private by default and retained only for a defined purpose.
6. Features should be added as coherent workflows, not decorative dashboard widgets.
