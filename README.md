# ResumeIQ — Talent Intelligence & Recruitment Operations

ResumeIQ is a local-first recruitment workspace for structured resume parsing, candidate review, job management, explainable matching, applications, interviews and recruitment analytics.

This archive is a clean development baseline. It is not a claim of production certification or validated hiring accuracy. Recruiters remain responsible for reviewing extracted information and making hiring decisions.

## Product modules

- **Resume ingestion:** PDF and DOCX validation, bounded document processing, text extraction, link discovery and optional OCR for scanned PDFs.
- **Structured parsing:** identity, contact details, profile summary, skills, employment, experience duration, education, projects, certifications, achievements, publications, languages and volunteering.
- **Evidence and review:** extraction confidence, source snippets, parser warnings, missing-field flags and editable candidate profiles.
- **Candidate CRM:** searchable profiles, original resume downloads, profile correction and duplicate protection.
- **Job management:** job descriptions, responsibilities, required/preferred skills, experience ranges and education requirements.
- **Applications:** six-stage workflow, recruiter notes and activity history.
- **Interviews:** scheduling, interview status and feedback scorecards.
- **Matching:** explainable baseline using skills, role text, experience and education. Scores are relevance estimates, not hiring decisions.
- **Analytics:** candidate, job, application, interview, skill and match summaries.
- **Optional supervised ranker:** trained only from reviewed labels with candidate-grouped hold-out evaluation. It is not automatically promoted.

## Visual direction

The interface uses the **Oxblood Chrome** design system: graphite surfaces, oxblood/ruby actions, titanium typography, steel-blue and muted secondary accents, spacious editorial layouts and restrained motion.

## Local setup prerequisites

The recommended local workflow uses the included setup scripts. A Windows environment with PowerShell, the required development runtimes, and Docker Desktop is supported.

## Windows setup — recommended

Extract the project into a clean directory. Run the one-time setup script from a PowerShell terminal opened at the project root:

```powershell
.\scripts\setup-windows.ps1
```

The script:

1. Checks that the required development runtimes and tools are available.
2. Creates the backend virtual environment.
3. Installs backend runtime and test dependencies.
4. Runs `pip check` and the backend test suite.
5. Creates `.env` from `.env.example` only if `.env` does not already exist.
6. Installs frontend packages and runs the Vite production build.
7. Validates the Compose configuration.

The script does not uninstall global software, delete existing project folders, or remove Docker volumes.

If PowerShell blocks script execution for the current terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup-windows.ps1
```

### Start development

After setup completes:

```powershell
.\scripts\start-windows.ps1
```

This starts the PostgreSQL container, launches FastAPI and Vite in separate PowerShell windows, and opens the frontend at its local address.

URLs:

- Frontend: <http://localhost:5173>
- Backend Swagger: <http://localhost:8000/docs>
- Backend health: <http://localhost:8000/api/health>
- PostgreSQL from Windows: `localhost:55432`

The database uses host port **55432** deliberately, to avoid colliding with the earlier prototype or another local PostgreSQL service on port 5432.

The Docker-published ports are bound to `127.0.0.1` by default so the unauthenticated local-development workspace is not exposed to other devices on the network. The Vite development and preview servers also bind to loopback. Do not change these bindings for a shared or public deployment without first enabling authentication and completing the security checklist.

To stop development, close the backend and frontend PowerShell windows, then from the project root run:

```powershell
.\scripts\stop-windows.ps1
```

This runs `docker compose down` without deleting persistent data.

## Full-stack Docker option

Create `.env` from `.env.example` if it does not exist, then from the project root:

```powershell
docker compose up --build
```

Open <http://localhost:8080>. The API is available at <http://localhost:8000>. Docker builds install the backend runtime and dependencies from the project configuration.

Stop without deleting persistent data:

```powershell
docker compose down
```

**The `docker compose down -v` command permanently deletes the database and resume-storage volumes.**

## OCR for scanned PDFs

Text-based PDFs and DOCX files work without OCR. OCR is optional and disabled by default. The Docker image includes Tesseract and the OCR Python dependencies; enable it by setting `OCR_ENABLED=true` in `.env` and rebuilding the backend image.

For native Windows development:

1. Install the Tesseract OCR executable separately.
2. From `backend`, install the optional Python dependencies:

   ```powershell
   python -m pip install -r requirements-ocr.txt
   ```
3. Set `OCR_ENABLED=true` and set `TESSERACT_CMD` to the full path of `tesseract.exe` in the root `.env`.
4. Restart the backend.

OCR is bounded by page and timeout limits. Scanned content can be less accurate than text-native PDFs and must be reviewed.

## Authentication and roles

Authentication is disabled by default for isolated local development. Before exposing the service to other users or a public network:

1. Set `AUTH_ENABLED=true`.
2. Replace `SECRET_KEY` with a random secret of at least 32 characters.
3. Set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` (minimum 12 characters), or use protected user management after an administrator exists.
4. Restart the backend and sign in.

Roles include admin, recruiter, reviewer and viewer. Do not expose the local-development configuration to the public internet. Production deployment still requires a security review, secure object storage, malware scanning, TLS, retention policy, monitoring and tenant-isolation testing.

## Database migrations

Local development defaults to `AUTO_CREATE_SCHEMA=true`. For controlled deployments, set it to `false`, then from `backend` run:

```powershell
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Add schema changes as new Alembic revisions. Do not rewrite migrations already applied to a shared database.

## Tests

From `backend` with its virtual environment active:

```powershell
python -m pytest -q
```

The suite uses isolated SQLite databases and temporary resume storage. It covers API CRUD, document upload validation, parser sections/date normalization, candidate correction, matching, applications, interviews, activity events and auth/role behavior.

## Supervised matching model

The default runtime uses the explainable hybrid baseline. It does not require a trained model artifact.

1. Copy `training/data/labeled_match_pairs.template.csv` to `training/data/labeled_match_pairs.csv`.
2. Add reviewed candidate/job relevance pairs. Use pseudonymous IDs and remove unnecessary personal information. Labels must be human-adjudicated (`1` relevant, `0` not relevant).
3. From the project root:

   ```powershell
   cd training
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python train_ranker.py
   ```

The trainer requires at least 50 reviewed pairs and 10 distinct candidate groups, then uses candidate-grouped hold-out validation. It reports classification and ranking metrics and saves a model candidate. It does not automatically promote the model. Do not use synthetic labels to claim hiring performance, and do not train on protected attributes or proxies for them.

## Licensing and release status

Review [`docs/THIRD_PARTY_LICENSES.md`](docs/THIRD_PARTY_LICENSES.md) before choosing a project license or distributing a public or commercial release. PyMuPDF is available under AGPL v3 or a separate commercial license; this choice matters for distribution.

## GitHub status

No GitHub repository is created, modified or published by these scripts. Review the code, configuration, tests and documentation first. Publish only after explicit approval.
