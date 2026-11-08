# Security and privacy notes

## Current protections

- Upload extension and PDF/DOCX signature checks.
- Upload size limit, PDF page cap, DOCX expanded-archive cap and bounded OCR processing.
- Randomized stored filenames outside the frontend static root.
- SHA-256 exact-file duplicate detection and normalized-email duplicate detection.
- Resume download handled through an API endpoint and bearer-token-aware frontend helper.
- Optional password hashing with PBKDF2-HMAC-SHA256 and signed HS256 access tokens.
- Role checks on write operations; viewers are read-only.
- Startup fails when authentication is enabled with the default/weak secret or an incomplete bootstrap credential pair.
- Database sessions and file storage are separated from the public frontend.
- `.env`, resume storage, databases, generated model files and frontend build outputs are ignored by Git.

## Important current limitations

- Authentication is optional and disabled by default for a local-only developer workspace.
- Access tokens are stored in browser localStorage. This is acceptable for local development but increases exposure if an XSS vulnerability is introduced. A hardened deployment should use short-lived access tokens, refresh-token rotation and a secure HttpOnly cookie/BFF pattern.
- Multi-tenant isolation is not implemented. The current database is a single workspace; do not expose it to multiple unrelated organizations.
- Resume files are stored on a private local Docker volume. Encryption at rest, malware scanning, antivirus scanning and object-store lifecycle rules are not implemented in this foundation.
- Activity events capture actor user ID/email for logged authenticated mutations, plus entity/action/time and structured metadata. They remain operational records, not a tamper-evident compliance audit system; request IP, immutable archival, and verified event integrity are not implemented.
- Rate limiting, brute-force lockout, account recovery, MFA and SSO are not implemented.
- Candidate data is highly sensitive. Use synthetic or consented test files until access control, retention, encryption, backup and legal/privacy requirements have been reviewed.

## Deployment checklist

- [ ] `AUTH_ENABLED=true` and a cryptographically random `SECRET_KEY` (32+ characters).
- [ ] Bootstrap admin credentials stored in a secrets manager, not `.env` committed to Git.
- [ ] Public sign-up disabled; least-privilege roles assigned.
- [ ] HTTPS enabled and CORS restricted to approved origins.
- [ ] PostgreSQL is not publicly exposed; credentials rotated.
- [ ] Private object storage, encryption, malware scanning and signed downloads configured.
- [ ] Retention and deletion schedules defined and tested.
- [ ] Backups encrypted and restore drill completed.
- [ ] Rate limits and failed-login protections enabled.
- [ ] Audit events include actor, target, time, request context and controlled access to logs.
- [ ] Tenant isolation implemented and tested before multiple organizations share the service.
- [ ] Matching policy, bias evaluation and human-review procedures approved.
