import re

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
