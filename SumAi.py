import os
import re
import json
from llama_cpp import Llama
from dotenv import load_dotenv
from Cleaner import clean_summary_text
from processor import extract_text_from_url

# ---------- Load environment variables ----------
load_dotenv(dotenv_path="./frontend/.env")
aipath = os.getenv("AI_PATH")

intern_s1 = os.path.join(aipath, "Intern-S1-mini-Q8_0.gguf")
medgemma = os.path.join(aipath, "medgemma-4b-it-Q4_K_M.gguf")

# ---------- Settings ----------
maxtokens = 512
temp = 0.5
topp = 0.9
repeatpenalty = 1.05

# Global cache
llm_instance = None


# ============================================================
# (1) MODEL LOADER
# ============================================================
def get_model(model="Intern-S1-mini-Q8_0.gguf"):
    global llm_instance
    if model == "medgemma-4b-it-Q4_K_M.gguf":
        llm_instance = Llama(
            model_path=medgemma,
            n_ctx=8192,
            n_threads=os.cpu_count(),
            n_batch=1024,
            n_gpu_layers=-1
        )
    else:
        if not os.path.exists(intern_s1):
            raise FileNotFoundError(f"Intern-S1 model not found at {intern_s1}")
        llm_instance = Llama(
            model_path=intern_s1,
            n_ctx=8192,
            n_threads=os.cpu_count(),
            n_batch=1024,
            n_gpu_layers=-1
        )
    return llm_instance


# ============================================================
# (2) IMAGE DESCRIPTION PLACEHOLDER
# ============================================================
def describe_images(images):
    return "\n".join([f"Image {os.path.basename(img)}: MRI scan or medical page." for img in images])


# ============================================================
# (3) CHUNK SUMMARIZATION LOGIC
# ============================================================
def summarize_chunk(chunk, idea, llm):
    prompt = f"""
You are SPARRC Summarizer AI, a helpful and friendly assistant for SPARRC Physiotherapy. Your tone is professional, empathetic, and clear. Your goal is to provide beautifully formatted, easy-to-read **summaries** of given content.

--- CONTENT TO SUMMARIZE ---
{chunk}
Doctor's Notes: {idea if idea else "None"}
--- END CONTENT ---

--- INSTRUCTIONS ---
1. **Summarize Faithfully:** Summarize ONLY the content provided above. Do not add new facts or assumptions.
2. **Summarization Style:**  
    - Use **simple, clear language** so that anyone can understand.  
    - Highlight only the **most important points** in the text.  
3. **Handle Unknowns Politely:** If the input is empty or unclear, respond with:  
    "I'm sorry, I couldn't find enough information to summarize right now. 😔"  
4. **Handle Distress or Emotional Content:** If the content expresses sadness, distress, or self-harm thoughts, summarize carefully and add an empathetic note at the end suggesting professional help.
5. **SPARRC Focus:** If the text contains both SPARRC and non-SPARRC info, focus mainly on **SPARRC-related** parts while briefly noting other parts if necessary.
6. **Formatting:** Use bullet points and headings to make the summary easy to read.
7. **Doctor's Notes:** The doctor's POV has to supported with claims if related information is correctly mentioned. Else just suppress this.
8. **sanitization:** Dont include any of the words mentions from INSTRUCTIONS. These are for you to help design perferct summary.
9. **Output Format:** Present the summary in well-structured bullet points grouped under relevant headings.
"""
    try:
        prt = llm.create_completion(
            prompt=prompt,
            max_tokens=maxtokens,
            temperature=temp,
            top_p=topp,
            repeat_penalty=repeatpenalty
        )
        if "choices" in prt and len(prt["choices"]) > 0:
            return prt["choices"][0]["text"].strip()
    except Exception as e:
        print(f"[ERROR] Summarization failed: {e}")
    return "[No output generated]"


# ============================================================
# (4) STRUCTURING FUNCTION (NEWLY ADDED)
# ============================================================
import re

def print_structured_summary(summary_text):
    # -------------------------
    # 1. Clean raw text
    # -------------------------
    text = summary_text.strip()
    text = re.sub(r"^(Here(?:’|'|)s a summary.*?:|Summary of .*?:)\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    # -------------------------
    # 2. Segment continuous summary into meaningful lines
    # -------------------------
    # Split into sentences and make each a line point
    sentences = re.split(r'(?<=[.!?])\s+', text)
    segmented_text = "\n".join([f"- {s.strip()}" for s in sentences if s.strip()])

    # Use segmented text for processing
    text = segmented_text

    # -------------------------
    # 3. Check if already structured (skip if model produced markdown)
    # -------------------------
    has_bullets = bool(re.search(r"^\s*[\*\-\•]\s", text, re.MULTILINE))
    has_headings = bool(re.search(r"\*\*.*\*\*", text))
    if has_bullets or has_headings:
        formatted = "\n".join([ln.strip() for ln in text.split("\n") if ln.strip()])
        return {
            "formatted_summary": f"========== SPARRC SUMMARY ==========\n\n{formatted}\n\n===================================",
            "structured": None
        }

    # -------------------------
    # 4. Pattern-based extraction
    # -------------------------
    name_match = re.search(r"([A-Z][a-z]+\s[A-Z][a-z]+)", text)
    age_match = re.search(r"(\d{1,2})[- ]?year[- ]?old", text)
    job_match = re.search(r"(IT professional|engineer|teacher|doctor|student|driver|manager|nurse|worker)", text, re.IGNORECASE)
    complaint_match = re.search(r"(low back pain|neck pain|shoulder pain|knee pain|disc bulge|sciatica|lumbar|cervical)", text, re.IGNORECASE)
    mri_match = re.search(r"(MRI|scan).*?(bulge|herniation|degeneration)", text, re.IGNORECASE)
    treatment_match = re.findall(r"(physiotherapy|painkiller|exercise|treatment|therapy|rest|heat pack)", text, re.IGNORECASE)
    posture_match = re.search(r"(slouched|poor posture|ergonomic chair)", text, re.IGNORECASE)
    impact_match = re.search(r"(sleep|productivity|daily activity|mobility|work)", text, re.IGNORECASE)

    structured = {
        "Patient Information": {
            "Name": name_match.group(1) if name_match else None,
            "Age": f"{age_match.group(1)} years" if age_match else None,
            "Occupation": job_match.group(1).capitalize() if job_match else None,
        },
        "Chief Complaint": complaint_match.group(1).capitalize() if complaint_match else "Not specified",
        "Findings / Diagnosis": mri_match.group(0) if mri_match else "No imaging info detected",
        "Symptoms": [s.strip().capitalize() for s in re.findall(r"(pain|numbness|stiffness|difficulty|ache|radiating|sharpness)[^.]*\.", text, re.IGNORECASE)] or ["Not clearly stated"],
        "Treatment History": list(set([t.capitalize() for t in treatment_match])) or ["None reported"],
        "Posture / Ergonomics": posture_match.group(1).capitalize() if posture_match else "Not mentioned",
        "Impact on Life": f"Affects {impact_match.group(1)}" if impact_match else "No explicit mention"
    }

    # -------------------------
    # 5. Construct clean formatted output
    # -------------------------
    formatted_lines = ["========== SUMMARY ==========\n"]
    for section, value in structured.items():
        formatted_lines.append(f"**{section}**")
        if isinstance(value, dict):
            for k, v in value.items():
                if v:
                    formatted_lines.append(f"- {k}: {v}")
        elif isinstance(value, list):
            for v in value:
                formatted_lines.append(f"- {v}")
        else:
            formatted_lines.append(f"- {value}")
        formatted_lines.append("")  # spacing
    # formatted_lines.append("===================================")

    # -------------------------
    # 6. Return final dict (tag-based output)
    # -------------------------
    # Build tag-based one-line-per-point output using <heading> and <point> tags.
    tag_lines = []
    for section, value in structured.items():
        tag_lines.append(f"<heading>{section}</heading>")
        if isinstance(value, dict):
            for k, v in value.items():
                if v:
                    # ensure single-line point
                    single_line = str(v).replace("\n", " ").strip()
                    tag_lines.append(f"<point>{k}: {single_line}</point>")
        elif isinstance(value, list):
            for v in value:
                single_line = str(v).replace("\n", " ").strip()
                tag_lines.append(f"<point>{single_line}</point>")
        else:
            single_line = str(value).replace("\n", " ").strip()
            tag_lines.append(f"<point>{single_line}</point>")

    # If we detected that the model already produced bullets/headings, convert those to tags
    if has_bullets or has_headings:
        converted = []
        for ln in text.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            # headings in bold **Heading** -> <heading>Heading</heading>
            bold_match = re.match(r"^\*\*(.+?)\*\*:?$", ln)
            if bold_match:
                converted.append(f"<heading>{bold_match.group(1).strip()}</heading>")
                continue
            # bullets - or * or • at line start
            bullet_match = re.match(r"^[\-\*\•]\s*(.+)$", ln)
            if bullet_match:
                converted.append(f"<point>{bullet_match.group(1).strip()}</point>")
                continue
            # plain line -> treat as point
            converted.append(f"<point>{ln}</point>")

        # prefer converted model output so we preserve model phrasing when available
        return {
            "formatted_summary": "\n".join(converted),
            "structured": None,
            "segmented_summary": text
        }

    return {
        "formatted_summary": "\n".join(tag_lines),
        "structured": structured,
        "segmented_summary": text  # add segmented raw version for debugging/inspection
    }



# ============================================================
# (5) MAIN SUMMARIZATION ENTRYPOINT
# ============================================================
def StartSummarize(path="", idea="", data="", form="false", pdf="false"):
    if form == "true" or pdf == "true":
        ext = extract_text_from_url(path)
        images, text = ext["images"], ext["text"]

        inp = clean_summary_text(text)
        llm = get_model()

        image_text = describe_images(images) if images else ""

        chunk_size = 5000
        chunks = [inp[i:i + chunk_size] for i in range(0, len(inp), chunk_size)]

        partial_summaries = []
        for idx, ch in enumerate(chunks):
            full_chunk = f"{ch}\n\nImage Information:\n{image_text}"
            summary = summarize_chunk(full_chunk, idea, llm)
            partial_summaries.append(summary)

        final_input = "\n".join(partial_summaries)
        final_summary = summarize_chunk(final_input, idea, llm)

    else:
        llm = get_model("medgemma-4b-it-Q4_K_M.gguf")
        print(f"\nUsing MedGemma (direct data mode)\n")

        try:
            prt = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a medical report summarizer."},
                    {"role": "user", "content": f"Summarize the following patient information:\n{data}"}
                ],
                max_tokens=maxtokens,
                temperature=temp,
                top_p=topp,
                repeat_penalty=repeatpenalty
            )

            if "choices" in prt and len(prt["choices"]) > 0:
                final_summary = prt["choices"][0]["message"]["content"].strip()
            else:
                final_summary = "[No output generated]"

        except Exception as e:
            print(f"[ERROR] MedGemma summarization failed: {e}")
            final_summary = "[Error in MedGemma output]"

    # ============================================================
    # STRUCTURED OUTPUT DISPLAY
    # ============================================================
    if final_summary and final_summary.strip() != "":
        print_structured_summary(final_summary)
    else:
        print("[Empty Summary]")

    return final_summary
