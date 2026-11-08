# ResumeIQ 2.2 — Talent Intelligence & Recruitment Operations

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

## Tested local toolchain target

Use the installed versions you reported:

| Tool | Local version | ResumeIQ selection |
|---|---:|---|
| Windows | Windows 11 x64 | Windows PowerShell |
| Python | 3.15.0 | Keep installed; not selected for this project |
| Python | 3.14.8 | **Selected for ResumeIQ** |
| pip | 26.3 | Upgrade via the project setup script |
| Node.js | 24.19.0 | Frontend runtime |
| npm | 12.2.1 | Frontend packages |
| Git | 2.55.0.windows.5 | Version control; no GitHub publishing is performed by setup |
| Docker | 29.7.2 | PostgreSQL and full-stack containers |
| Docker Compose | 5.5.0 | Local services |
| VS Code | 1.145.2 | Recommended editor |

### Why Python 3.14.8 for this project?

The previous installation selected PyMuPDF 2.x, which pulled ONNX Runtime into the PDF dependency chain. ONNX Runtime does not yet publish a compatible Windows wheel for the user's Python 3.15 environment. This rebuild pins **PyMuPDF 1.26.7**, which has Windows `abi3` wheels, requires Python 3.10 or later and has no mandatory ONNX Runtime dependency. We still select Python 3.14.8 because PyMuPDF 1.26.x documents support through Python 3.14. This avoids relying on an unverified Python 3.15 combination.

Sources: [PyMuPDF 1.26.7 on PyPI](https://pypi.org/project/pymupdf/1.26.7/) · [PyMuPDF installation documentation](https://pymupdf.readthedocs.io/en/latest/installation.html) · [ONNX Runtime wheel files](https://pypi.org/project/onnxruntime/)

Do not replace the PyMuPDF pin with `pymupdf>=2.1` or add `pymupdf-layout` without checking the ONNX Runtime wheel matrix first.

## Windows setup — recommended

Extract this archive into a **new folder** so the earlier prototype and its virtual environments are not mixed with this rebuild. Suggested path:

```text
C:\Users\ray\Downloads\ResumeIQ-Clean
```

Open this folder in VS Code. In the integrated PowerShell terminal, run the one-time setup script:

```powershell
.\scripts\setup-windows.ps1
```

The script:

1. Verifies Python 3.14, Node.js, npm and Docker are available.
2. Creates `backend\.venv` with Python 3.14.
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

This starts the PostgreSQL container, opens separate PowerShell windows for FastAPI and Vite, and opens the frontend in your browser.

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

## Manual Windows setup (alternative)

From the project root, create `.env` once:

```powershell
Copy-Item .env.example .env
```

Start PostgreSQL:

```powershell
docker compose up -d db
```

Backend terminal:

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Frontend terminal:

```powershell
cd frontend
npm install
npm run dev
```

## Full-stack Docker option

Create `.env` from `.env.example` if it does not exist, then from the project root:

```powershell
docker compose up --build
```

Open <http://localhost:8080>. The API is available at <http://localhost:8000>. Docker builds use Python 3.14 and install the same pinned PyMuPDF 1.26.7 dependency family.

Stop without deleting persistent data:

```powershell
docker compose down
```

**Do not run `docker compose down -v` unless you intentionally want to delete the new database and resume-storage volumes.**

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
   py -3.14 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python train_ranker.py
   ```

The trainer requires at least 50 reviewed pairs and 10 distinct candidate groups, then uses candidate-grouped hold-out validation. It reports classification and ranking metrics and saves a model candidate. It does not automatically promote the model. Do not use synthetic labels to claim hiring performance, and do not train on protected attributes or proxies for them.

## Licensing and release status

Review [`docs/THIRD_PARTY_LICENSES.md`](docs/THIRD_PARTY_LICENSES.md) before choosing a project license or distributing a public/commercial release. PyMuPDF 1.26.7 is available under AGPL v3 or a separate commercial license; this choice matters for distribution.

## GitHub status

No GitHub repository is created, modified or published by these scripts. Review the code, configuration, tests and documentation first. Publish only after explicit approval.
