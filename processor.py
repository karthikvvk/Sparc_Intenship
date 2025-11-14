from transformers import pipeline
from pdf2image import convert_from_path
import pytesseract
import tempfile
import os
from concurrent.futures import ProcessPoolExecutor, as_completed# fro multi threaded extraction
import multiprocessing
import fitz  # PyMuPDF package
import re


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
                # print(ocr_text)
                page_texts.append(f"--- Page {page_num} ---\n{ocr_text.strip()}\n")

                # Save full page image too for record
                full_img_path = os.path.join(img_dir, f"page_{page_num}_full.png")
                img.save(full_img_path)
                all_images.append(full_img_path)

            # #Extract additional embedded images (optional)
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
    # print([all_images, text])
    return {"images": all_images, "text": text}


def droper(summary):
    pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v0.6")
    messages = [
        {"role": "user", "content": f"""
    You are a droping + cleaner model. so remove any thought process or the reasoning steps from the input and provide only the final structured data output.
    make sure whole detail is covered.
    structure output point wise.
    output should be smaller than the input.
    so dont include any of your though process and remove any such from the input.


    input:{summary}
    """},
    ]
   
    output = pipe(messages)

    # HF pipeline returns list → extract 0th element
    first = output[0]

    # TinyLlama returns inside first["generated_text"]
    generated_list = first.get("generated_text", [])

    # Find assistant response
    cleaned = ""
    for item in generated_list:
        role = item.get("role", "")
        if role == "assistant":
            cleaned = item.get("content", "")
            break

    return cleaned.strip()


def print_structured_summary(summary_text):
    text = summary_text.strip()

    # ---------------------------------------------------------
    # Detect headings like "summary:", "symptoms:" etc
    # ---------------------------------------------------------
    if re.search(r"^(summary|symptoms|history|treatment|environment):",
                 text, re.IGNORECASE | re.MULTILINE):

        lines = text.split("\n")
        current_heading = None
        html_output = []
        current_list = []

        for line in lines:
            line = line.strip()

            # Detect heading
            match = re.match(r"^(summary|symptoms|history|treatment|environment):",
                             line, re.IGNORECASE)
            if match:
                # If previous list exists → flush it
                if len(current_list) > 0:
                    html_output.append("<ul>")
                    for item in current_list:
                        html_output.append("<li>" + item + "</li>")
                    html_output.append("</ul>")
                    current_list = []

                # Add heading
                current_heading = match.group(1).capitalize()
                html_output.append("<h2>" + current_heading + "</h2>")
                continue

            # Detect point (bullet)
            if line.startswith("-") or line.startswith("•"):
                point = line.lstrip("-• ").strip()
                if point != "":
                    current_list.append(point)
                continue

            # Plain text under heading → treat as list item
            if current_heading is not None and line != "":
                current_list.append(line)

        # Flush last list
        if len(current_list) > 0:
            html_output.append("<ul>")
            for item in current_list:
                html_output.append("<li>" + item + "</li>")
            html_output.append("</ul>")

        final_html = "\n".join(html_output)

        return {
            "formatted_summary": final_html,
            "structured": None
        }

    # ---------------------------------------------------------
    # CASE 2: Plain sentence summary → wrap everything in <ul><li>
    # ---------------------------------------------------------
    sentences = re.split(r'(?<=[.!?])\s+', text)

    html_output = []
    html_output.append("<h2>Summary</h2>")
    html_output.append("<ul>")

    for s in sentences:
        sentence = s.strip()
        if sentence != "":
            html_output.append("<li>" + sentence + "</li>")

    html_output.append("</ul>")

    final_html = "\n".join(html_output)

    return {
        "formatted_summary": final_html,
        "structured": None
    }


def clean_summary_text(raw_text: str) -> str:
    """
    Cleans extracted text for medical summarization:
    - Removes AI meta tags (<|...|>, assistant, final, etc.)
    - Normalizes spaces, newlines, punctuation
    - Strips markdown, HTML tags, quotes
    - Preserves medically relevant text only
    - Returns a single clean paragraph
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Remove HTML tags and markdown
    text = re.sub(r'<[^>]+>', ' ', text)            # HTML tags
    text = re.sub(r'[*_`~#>\-]', ' ', text)         # markdown symbols like *, _, `, ~, #

    # 2. Remove AI meta markers and tokens
    text = re.sub(r'<\|.*?\|>', ' ', text)          # <|start|>, <|end|>, etc.
    text = re.sub(r'\b(?:assistant|final|message|channel|start|end)\b', ' ', text, flags=re.IGNORECASE)

    # 3. Remove control/non-ASCII characters but keep punctuation
    text = re.sub(r'[^\x20-\x7E\n]', ' ', text)

    # 4. Normalize line breaks and collapse multiple spaces
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # 5. Clean up quotes and repeated punctuation
    text = re.sub(r'[“”"“”]', '', text)
    text = re.sub(r'([.!?]){2,}', r'\1', text)      # e.g., "!!!" -> "!"

    # 6. Trim leading/trailing spaces
    text = text.strip()

    return text
