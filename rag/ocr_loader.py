import os
from PIL import Image
from langchain_core.documents import Document
from rag.loader import load_pdf

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image file using OCR.
    Tries pytesseract first, then easyocr as fallback.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Try pytesseract
    try:
        import pytesseract
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"pytesseract extraction attempt failed or not configured: {e}")

    # Fallback to easyocr
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(image_path, detail=0)
        text = "\n".join(results)
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"easyocr extraction attempt failed: {e}")

    # Fallback message if OCR engines are unavailable
    return (
        f"[OCR Warning: Text extraction attempted for {os.path.basename(image_path)}. "
        "Please ensure 'pytesseract' with Tesseract-OCR or 'easyocr' is installed for full OCR functionality.]"
    )


def load_photo_ocr(image_path: str) -> list[Document]:
    """
    Load a single image/photo, perform OCR, and return a list containing a LangChain Document.
    """
    text = extract_text_from_image(image_path)
    document = Document(
        page_content=text,
        metadata={
            "source": image_path,
            "page": 1,
            "filename": os.path.basename(image_path),
            "file_type": "photo_ocr"
        }
    )
    return [document]


def load_photos_ocr(image_paths: list[str]) -> list[Document]:
    """
    Load multiple image/photo files, perform OCR on each, and return list of Documents.
    """
    documents = []
    for idx, path in enumerate(image_paths, start=1):
        if not os.path.exists(path):
            continue
        text = extract_text_from_image(path)
        doc = Document(
            page_content=text,
            metadata={
                "source": path,
                "page": idx,
                "filename": os.path.basename(path),
                "file_type": "photo_ocr"
            }
        )
        documents.append(doc)
    return documents


def load_any_document(file_path: str) -> list[Document]:
    """
    Unified document loader:
    Supports PDFs via load_pdf and Photos/Images via load_photo_ocr.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in IMAGE_EXTENSIONS:
        return load_photo_ocr(file_path)
    else:
        raise ValueError(f"Unsupported file extension '{ext}'. Supported: .pdf, {', '.join(sorted(IMAGE_EXTENSIONS))}")
