# =============================================================
# utils/file_parser.py
# Multi-format resume ingestion: routes uploaded files (PDF, DOCX,
# CSV) and ZIP archives of the same to the correct in-memory parser.
# =============================================================

import io
import re
import zipfile

import pandas as pd
from docx import Document

from utils.pdf_parser import extract_text_from_pdf

SUPPORTED_EXTENSIONS = ("pdf", "docx", "csv")

# Columns that commonly hold resume-like free text in a candidate CSV export
CSV_TEXT_COLUMNS = ["Resume Text", "Experience", "Skills", "Summary", "Education"]
CSV_NAME_COLUMNS = ["Name", "Candidate Name", "Full Name"]

# Boilerplate lines commonly injected by resume templates / PDF-DOCX exporters that
# add no scoring signal for the LLM - dropped outright rather than just trimmed
_BOILERPLATE_LINE_PATTERNS = [
    re.compile(r"^page\s+\d+(\s*of\s*\d+)?$", re.IGNORECASE),
    re.compile(r"^references available upon request\.?$", re.IGNORECASE),
    re.compile(r"^confidential$", re.IGNORECASE),
    re.compile(r"^curriculum vitae$", re.IGNORECASE),
]


def extract_text_from_docx(file_stream) -> str:
    """
    Extract all paragraph and table cell text from a Word (.docx) file stream.

    Args:
        file_stream: A .docx source - a file-like object (BytesIO or Streamlit
            UploadedFile), or raw bytes (e.g. a ZIP archive entry read via
            `archive.open(...).read()`). Raw bytes are wrapped in `io.BytesIO`
            since `docx.Document()` only accepts a stream, not bytes directly.

    Returns:
        str: All paragraph and table cell text joined by newlines, or an error message string
    """
    try:
        if isinstance(file_stream, (bytes, bytearray)):
            file_stream = io.BytesIO(file_stream)

        document = Document(file_stream)

        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]

        table_cell_texts = [
            cell.text.strip()
            for table in document.tables
            for row in table.rows
            for cell in row.cells
            if cell.text.strip()
        ]

        full_text = "\n".join(paragraphs + table_cell_texts)

        if len(full_text.strip()) < 50:
            return (
                "Warning: Very little text was extracted from this Word document.\n\n"
                + full_text
            )

        return full_text

    except Exception as e:
        return f"Error reading DOCX: {str(e)}. Please ensure the file is a valid Word document."


def _row_to_profile_text(row: pd.Series) -> str:
    """Combines the free-text columns of a CSV row into a single resume-like payload,
    falling back to every column when none of the well-known text columns are present."""
    text_parts = [
        f"{column}: {row[column]}"
        for column in CSV_TEXT_COLUMNS
        if column in row.index and pd.notna(row[column]) and str(row[column]).strip()
    ]
    if text_parts:
        return "\n".join(text_parts)

    return "\n".join(
        f"{column}: {value}" for column, value in row.items() if pd.notna(value) and str(value).strip()
    )


def extract_text_from_csv(file_stream) -> list:
    """
    Parse a CSV of candidate records into one text profile per row.

    Args:
        file_stream: A file-like object (BytesIO or Streamlit UploadedFile) containing candidate rows

    Returns:
        list[tuple[str, str]]: (candidate_label, profile_text) pairs, one per data row.
        Falls back to a single-element error-message pair if the file can't be parsed.
    """
    try:
        dataframe = pd.read_csv(file_stream)

        if dataframe.empty:
            return [("Empty CSV", "Error: The CSV file contains no rows.")]

        name_column = next((c for c in CSV_NAME_COLUMNS if c in dataframe.columns), None)

        records = []
        for row_idx, row in dataframe.iterrows():
            candidate_label = (
                str(row[name_column]).strip()
                if name_column and pd.notna(row[name_column])
                else f"Candidate Row {row_idx + 1}"
            )
            records.append((candidate_label, _row_to_profile_text(row)))

        return records

    except Exception as e:
        return [("CSV Parse Error", f"Error reading CSV: {str(e)}. Please ensure the file is a valid CSV.")]


def extract_essential_resume_text(raw_text: str) -> str:
    """
    Cleans raw parser output (from PDF/DOCX/CSV) down to a high-density payload
    before it is sent to an LLM: strips non-printable characters and page-break
    markers, collapses tab indentation and repeated spaces, drops known export
    boilerplate lines (page numbers, "References available upon request", etc.),
    and squashes duplicate blank lines. No section content is ever removed - only
    formatting noise - so Professional Summary, Work Experience, Skills, Projects,
    Certifications, and Education all pass through intact. A smaller, denser
    payload means fewer input tokens are spent on noise, leaving more of the
    model's output budget available for a complete, untruncated response.

    Args:
        raw_text: The raw text pulled from a PDF/DOCX/CSV parser

    Returns:
        str: A cleaned, high-density version of the same text
    """
    if not raw_text:
        return ""

    # Normalize page-break/form-feed markers and line endings, then drop
    # non-printable control characters (keep newlines and tabs for now - the
    # tab-collapsing step below normalizes those)
    text = raw_text.replace("\x0c", "\n").replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch in ("\n", "\t") or ch.isprintable())

    # Tab indentation and runs of horizontal whitespace -> a single space
    text = re.sub(r"[ \t]+", " ", text)

    cleaned_lines = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if line and any(pattern.match(line) for pattern in _BOILERPLATE_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)

    # Collapse runs of 2+ consecutive blank lines down to a single separator
    deduplicated_lines = []
    for line in cleaned_lines:
        if line == "" and deduplicated_lines and deduplicated_lines[-1] == "":
            continue
        deduplicated_lines.append(line)

    return "\n".join(deduplicated_lines).strip()


def parse_resume_file(file_obj, filename: str) -> list:
    """
    Unified dispatcher that routes an uploaded file to the correct parser based on its
    extension and normalizes the result into a list of (label, text) records - a
    single-element list for PDF/DOCX, potentially multi-element for CSV (one row per
    candidate).

    Args:
        file_obj: A file-like object (BytesIO or Streamlit UploadedFile)
        filename: The original file name, used to determine the parser via extension

    Returns:
        list[tuple[str, str]]: (candidate_label, extracted_text) pairs
    """
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if extension == "pdf":
        return [(filename, extract_text_from_pdf(file_obj))]
    if extension == "docx":
        return [(filename, extract_text_from_docx(file_obj))]
    if extension == "csv":
        return extract_text_from_csv(file_obj)

    return [(filename, f"Error: Unsupported file type '.{extension}'. Supported formats: PDF, DOCX, CSV.")]


def extract_texts_from_zip(uploaded_zip_file) -> list:
    """
    Extract text content from every supported resume file (.pdf, .docx, .csv) found
    inside an uploaded ZIP archive. Everything happens in memory via `zipfile`/`io.BytesIO`
    - no extracted file is ever written to disk.

    Args:
        uploaded_zip_file: Streamlit UploadedFile object (the ZIP archive)

    Returns:
        list[tuple[str, str]]: (file_name, extracted_text) pairs. CSV entries may
        contribute multiple pairs (one per candidate row) from a single archive entry.
    """
    extracted_records = []

    zip_bytes = io.BytesIO(uploaded_zip_file.read())
    with zipfile.ZipFile(zip_bytes) as archive:
        for entry_info in archive.infolist():
            # Skip directory entries entirely
            if entry_info.is_dir():
                continue

            entry_name = entry_info.filename
            base_name = entry_name.rsplit("/", 1)[-1]

            # Skip OS/junk files (e.g. __MACOSX, .DS_Store) and unsupported extensions
            if base_name.startswith("."):
                continue

            extension = base_name.lower().rsplit(".", 1)[-1] if "." in base_name else ""
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            with archive.open(entry_info) as entry_file:
                entry_stream = io.BytesIO(entry_file.read())

            extracted_records.extend(parse_resume_file(entry_stream, base_name))

    return extracted_records
