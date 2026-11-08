# Third-party licensing notes

This document is a starting point for release review, not legal advice.

## Important dependency notice

ResumeIQ currently uses PyMuPDF 1.26.7 for PDF text extraction and rendering. PyMuPDF is offered under the GNU AGPL v3 or a separate commercial license by Artifex. Before distributing ResumeIQ as a proprietary/commercial service or publishing a differently licensed combined distribution, review the PyMuPDF license terms and obtain legal advice or the appropriate commercial license where required.

Official references:

- https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright
- https://pypi.org/project/pymupdf/1.26.7/

Other dependencies retain their own licenses. Generate a complete dependency license inventory as part of release preparation; this file is not a complete license manifest.

## Release gate

- [ ] Decide the project's own license.
- [ ] Generate and review licenses for every pinned/transitive Python and npm dependency.
- [ ] Confirm PyMuPDF use is consistent with the project's distribution model.
- [ ] Include required third-party notices in packaged releases.
