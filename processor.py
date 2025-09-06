from pdf2image import convert_from_path
import pytesseract
import tempfile
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


def _ocr_page(idx, img, lang):
    """Helper function to OCR one page."""
    page_text = pytesseract.image_to_string(img, lang=lang)
    return f"--- Page {idx+1} ---\n{page_text.strip()}\n"


def extract_text_from_url(pdf_path, dpi=300, lang="eng"):
    """
    Extract text from a PDF using OCR in parallel.
    
    Args:
        pdf_path (str): Path to PDF file
        dpi (int): Resolution for PDF to image conversion
        lang (str): Language for Tesseract OCR
    
    Returns:
        tuple: (text, file_ext)
    """
    print("extracting text from PDF...")
    text_output = []

    with tempfile.TemporaryDirectory() as path:
        # Convert all pages to images (parallelized internally)
        images = convert_from_path(pdf_path, dpi=dpi, output_folder=path, thread_count=multiprocessing.cpu_count())

        # OCR pages in parallel
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = [executor.submit(_ocr_page, i, img, lang) for i, img in enumerate(images)]
            for f in as_completed(futures):
                text_output.append(f.result())

    # Keep order (as_completed shuffles results)
    text_output.sort(key=lambda x: int(x.split("Page ")[1].split(" ---")[0]))

    text = "\n".join(text_output)
    file_ext = os.path.splitext(pdf_path)[-1].lower()
    return text, file_ext
