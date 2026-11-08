from __future__ import annotations

import io
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from docx import Document

from app.core.config import settings


@dataclass(slots=True)
class DocumentContent:
    text: str
    pages: list[str]
    page_count: int
    extraction_method: str
    warnings: list[str]
    links: list[str]


def _extract_docx(content: bytes) -> DocumentContent:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ValueError("The file is not a valid DOCX document.")
            if len(names) > 2500 or sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
                raise ValueError("The DOCX archive expands beyond the safe processing limit.")
    except zipfile.BadZipFile as exc:
        raise ValueError("The DOCX file is damaged or is not a valid Office document.") from exc
    document = Document(io.BytesIO(content))
    lines: list[str] = []
    for paragraph in document.paragraphs:
        value = re.sub(r"\s+", " ", paragraph.text).strip()
        if value:
            lines.append(value)
    for table in document.tables:
        for row in table.rows:
            cells = [re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells]
            if any(cells):
                lines.append(" | ".join(cells))
    links: list[str] = []
    rels = document.part.rels.values()
    for rel in rels:
        if "hyperlink" in rel.reltype and rel.target_ref.startswith(("http://", "https://", "mailto:")):
            links.append(rel.target_ref)
    text = "\n".join(lines).strip()
    return DocumentContent(text=text, pages=[text] if text else [], page_count=0, extraction_method="docx-text", warnings=[], links=sorted(set(links)))


def _extract_pdf(content: bytes) -> DocumentContent:
    pages: list[str] = []
    warnings: list[str] = []
    links: list[str] = []
    ocr_used = False
    with pymupdf.open(stream=content, filetype="pdf") as pdf:
        if pdf.is_encrypted:
            raise ValueError("This PDF is password protected. Upload an unlocked copy.")
        page_count = len(pdf)
        if page_count == 0:
            raise ValueError("The PDF contains no pages.")
        if page_count > 80:
            raise ValueError("This PDF exceeds the 80-page resume processing limit. Upload a shorter resume document.")
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text", sort=True).strip()
            for link in page.get_links():
                uri = link.get("uri")
                if uri and uri.startswith(("http://", "https://", "mailto:")):
                    links.append(uri)
            if len(text) < 25 and settings.ocr_enabled:
                try:
                    import pytesseract
                    from PIL import Image
                    if settings.tesseract_cmd:
                        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
                    if not shutil.which("tesseract") and not Path(settings.tesseract_cmd).is_file():
                        raise RuntimeError("Tesseract executable is unavailable")
                    if page_number > 20:
                        warnings.append(f"Page {page_number}: OCR page limit reached; this page was not OCR-processed.")
                        pages.append(text)
                        continue
                    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(image, timeout=15).strip()
                    if ocr_text:
                        text = ocr_text
                        ocr_used = True
                except Exception as exc:
                    warnings.append(f"Page {page_number}: OCR could not run ({str(exc)[:100]}).")
            pages.append(text)
    full_text = "\n\n".join(f"[PAGE {index}]\n{page}" for index, page in enumerate(pages, start=1) if page).strip()
    if not any(page.strip() for page in pages):
        if settings.ocr_enabled:
            raise ValueError("No readable text was found, even after OCR. Try a clearer scan.")
        raise ValueError("No selectable text was found. This appears to be a scanned PDF; enable OCR or upload a text-based PDF.")
    return DocumentContent(
        text=full_text,
        pages=pages,
        page_count=page_count,
        extraction_method="pdf-text+ocr" if ocr_used else "pdf-text",
        warnings=warnings,
        links=sorted(set(links)),
    )


def read_document(filename: str, content: bytes) -> DocumentContent:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise ValueError("Unsupported file. Upload a PDF or DOCX resume.")
    if not content:
        raise ValueError("The uploaded document is empty.")
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("The file extension says PDF, but its contents are not a valid PDF.")
        try:
            return _extract_pdf(content)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("The PDF could not be read. It may be damaged, encrypted or use unsupported features.") from exc
    if not content.startswith(b"PK"):
        raise ValueError("The file extension says DOCX, but its contents are not a valid Office document.")
    try:
        return _extract_docx(content)
    except Exception as exc:
        raise ValueError(f"The DOCX document could not be read: {str(exc)[:160]}") from exc
