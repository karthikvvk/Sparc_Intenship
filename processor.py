from pdf2image import convert_from_path
import pytesseract
import tempfile
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import fitz  # PyMuPDF


def _ocr_page(idx, img, lang):
    """Helper function to OCR one page."""
    page_text = pytesseract.image_to_string(img, lang=lang)
    return idx, f"--- Page {idx+1} ---\n{page_text.strip()}\n"

def extract_text_from_url(pdf_path, output_dir="./extracted", dpi=300, lang="eng"):
    import shutil
    os.makedirs(output_dir, exist_ok=True)
    text_dir = os.path.join(output_dir, "text")
    img_dir = os.path.join(output_dir, "images", os.path.splitext(os.path.basename(pdf_path))[0])

    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    all_images = []
    page_texts = []

    with tempfile.TemporaryDirectory() as path:
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()

            # Case 1: Embedded text present
            if page_text:
                page_texts.append(f"--- Page {page_num} ---\n{page_text}\n")
            else:
                # Case 2: Full page OCR
                raster_imgs = convert_from_path(
                    pdf_path, dpi=dpi, first_page=page_num, last_page=page_num,
                    output_folder=path, thread_count=1
                )
                img = raster_imgs[0]

                ocr_text = pytesseract.image_to_string(img, lang=lang)
                print(ocr_text)
                page_texts.append(f"--- Page {page_num} ---\n{ocr_text.strip()}\n")

                # Save full page image too for record
                full_img_path = os.path.join(img_dir, f"page_{page_num}_full.png")
                img.save(full_img_path)
                all_images.append(full_img_path)

            # Extract additional embedded images (optional)
            # for img_index, img_meta in enumerate(page.get_images(full=True)):
            #     xref = img_meta[0]
            #     pix = fitz.Pixmap(doc, xref)
            #     img_file = os.path.join(img_dir, f"page_{page_num}_img_{img_index+1}.png")

            #     if pix.n < 5:  # GRAY/RGB
            #         pix.save(img_file)
            #     else:  # CMYK -> convert
            #         pix = fitz.Pixmap(fitz.csRGB, pix)
            #         pix.save(img_file)

            #     all_images.append(img_file)

    text = "\n".join(page_texts)
    print([all_images, text])
    return {"images": all_images, "text": text}
