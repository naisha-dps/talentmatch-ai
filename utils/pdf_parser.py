# =============================================================
# utils/pdf_parser.py
# Handles PDF resume parsing using pypdf library
# =============================================================

import io
from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract all text content from an uploaded PDF file.

    Args:
        uploaded_file: Streamlit UploadedFile object (the PDF)

    Returns:
        str: Extracted text from the PDF, or error message string
    """
    try:
        # Read the uploaded file bytes into memory
        # Streamlit's UploadedFile needs to be wrapped in BytesIO for pypdf
        pdf_bytes = io.BytesIO(uploaded_file.read())

        # Create a PdfReader object from the byte stream
        reader = PdfReader(pdf_bytes)

        # Check if the PDF has any pages
        if len(reader.pages) == 0:
            return "Error: The PDF file appears to be empty."

        # Collect text from every page
        extracted_text = []
        for page_num, page in enumerate(reader.pages):
            # extract_text() pulls raw text from each page
            page_text = page.extract_text()
            if page_text:
                extracted_text.append(page_text)

        # Join all pages with a newline separator
        full_text = "\n".join(extracted_text)

        # Basic validation - if almost no text was extracted, warn the user
        if len(full_text.strip()) < 50:
            return (
                "Warning: Very little text was extracted. "
                "The PDF might be image-based (scanned). "
                "Please use a text-based PDF for best results.\n\n"
                + full_text
            )

        return full_text

    except Exception as e:
        # Catch any pypdf or IO errors and return a friendly message
        return f"Error reading PDF: {str(e)}. Please ensure the file is a valid PDF."


def get_pdf_metadata(uploaded_file) -> dict:
    """
    Extract metadata (author, title, pages) from a PDF file.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        dict: Metadata fields from the PDF
    """
    try:
        pdf_bytes = io.BytesIO(uploaded_file.read())
        reader = PdfReader(pdf_bytes)

        metadata = {
            "pages": len(reader.pages),
            "title": reader.metadata.title if reader.metadata else "Unknown",
            "author": reader.metadata.author if reader.metadata else "Unknown",
        }
        return metadata

    except Exception as e:
        return {"pages": "Unknown", "title": "Unknown", "author": "Unknown", "error": str(e)}
