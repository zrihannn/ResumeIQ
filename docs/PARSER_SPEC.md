# Resume parser specification

## Supported inputs

- `.pdf`: text extraction using PyMuPDF; optional OCR for image-only pages when enabled.
- `.docx`: paragraph, table and hyperlink extraction using python-docx.
- Default upload limit: 15 MB.
- PDF page limit: 80.
- Optional OCR page limit: 20 pages per file, with a per-page timeout.

Legacy `.doc`, image-only uploads and other office formats are not accepted by the current API.

## Structured output

### Identity and contact

- Full, first and last name (when inferable)
- Email and phone
- Location text
- Professional links such as LinkedIn, GitHub, GitLab, Behance, Dribbble and portfolio URLs

### Professional profile

- Professional headline
- Summary/objective
- Estimated total experience in years

### Skills

- Canonical technical skill names using aliases
- Soft skills from a curated taxonomy
- Tools and platforms
- Technologies mentioned in projects and experience entries

### Experience

- Role/title
- Employer where the heading supports it
- Start and end dates normalized to `YYYY-MM` or `YYYY`
- Current-role indicator
- Estimated duration in months
- Responsibilities
- Technologies

### Education

- Degree/qualification
- Field of study / specialization
- Institution where identifiable
- Start and end/completion date where present
- Grade, GPA, CGPA or percentage where present

### Other sections

- Projects with description and detected technologies
- Certifications with name, issuer, credential identifier and available issue/expiry dates
- Achievements and awards
- Publications/research
- Languages with detected proficiency labels
- Volunteering/community involvement

## Evidence and confidence

Each major profile field includes an evidence object where it can be located:

- `value`
- `snippet`
- `line`
- `page` (PDF page where page markers are available)
- `confidence` (parser heuristic confidence, not a statistical probability)
- `method` (pattern, text-context or inference)

Experience, education, project and simple-section entries carry a local `evidence` object. This provides reviewers with an original snippet to compare against the parsed value.

Confidence is intentionally labelled as a heuristic signal. It is not calibrated until evaluated against a manually annotated resume corpus.

## Date normalization and experience calculation

Accepted date forms include month names (`Jan 2022`), numeric month/year (`01/2022`, `01-2022`), year-month (`2022-01`) and year-only (`2022`). `Present`, `Current` and `Now` normalize to `present`.

When date ranges can be identified, experience duration is estimated from month-level intervals. Overlapping roles are merged so concurrent work is not double-counted. If only a stated total experience phrase is available, that value is used as a fallback. Ambiguous dates or profiles should be reviewed by a recruiter.

## Review warnings

The parser adds warnings for missing/uncertain name and email, absent experience/education sections and an unknown/empty skill vocabulary result. It estimates completeness and section coverage, then sets `requires_review` for low-confidence or incomplete profiles.

## Duplicate protection

- Exact file duplicates are detected by SHA-256 checksum.
- Existing candidates with the same normalized email are flagged.
- A duplicate does not silently overwrite the previous candidate; a recruiter should inspect the existing profile first.

## Known limitations

This parser is a deterministic, section-aware extraction baseline. It does not yet use an LLM or trained named-entity recognition model. Complex two-column layouts, unusual headings, image-embedded text, scanned files without OCR, tables with visual reading order, multilingual resumes, fragmented education/certification records and unusual date phrases can reduce extraction quality. Education and certification grouping is heuristic: recruiters should verify linked fields against the source snippet. The parser therefore preserves source documents, evidence and manual correction rather than claiming perfect extraction.
