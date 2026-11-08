# Build and dependency decisions — ResumeIQ 2.2

## Previous setup failure

The preceding requirements allowed PyMuPDF 2.x. The selected release pulled ONNX Runtime into the PDF processing dependency chain. The package index did not provide a compatible Windows ONNX Runtime wheel for the installed CPython 3.15.0, so pip stopped before finishing the backend install. Uvicorn was consequently absent from that incomplete environment.

## Decisions in this clean rebuild

- Use the installed Python 3.14.8 for this project; leave global Python 3.15.0 installed for other work.
- Pin PyMuPDF to 1.26.7. It has Windows x64 stable-ABI wheels, supports Python 3.10 through 3.14 in its documented support matrix, and has no mandatory ONNX Runtime dependency.
- Keep OCR Python dependencies separate in `requirements-ocr.txt`; OCR is optional and disabled by default.
- Use PostgreSQL host port 55432 so this project does not collide with the previous prototype on 5432.
- Give this Compose stack its own project name and named volumes.
- Use a clean folder and a new `backend/.venv`; never reuse the failed 3.15 virtual environment.

## Local validation in the build environment

- Backend tests: 17 passed.
- Python compile check: passed.
- JSX parser check: 0 parse diagnostics.
- CSS parser: 0 parse errors.
- Compose YAML: parsed; services `db`, `backend`, `frontend` present.
- Full npm install/build: not completed in the build environment because npm registry access timed out. The Windows setup script runs `npm install` and `npm run build` on the user's PC and stops if either fails.
