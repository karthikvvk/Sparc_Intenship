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
current_model_name = None


# ============================================================
# (1) MODEL LOADER
# ============================================================
def get_model(model="Intern-S1-mini-Q8_0.gguf"):
    """
    Loads the appropriate Llama model instance:
    - Intern-S1: via new Llama.from_pretrained
    - MedGemma: via classic Llama(model_path)
    """
    global llm_instance, current_model_name

    if model == "medgemma-4b-it-Q4_K_M.gguf":
        current_model_name = "medgemma"
        llm_instance = Llama(
            model_path=medgemma,
            n_ctx=8192,
            n_threads=os.cpu_count(),
            n_batch=1024,
            n_gpu_layers=-1
        )
        print("[Loaded MedGemma 4B]")
    else:
        current_model_name = "internlm"
        if not os.path.exists(intern_s1):
            raise FileNotFoundError(f"Intern-S1 model not found at {intern_s1}")

        print("\n[Loading Intern-S1 using new llama-cpp API]\n")
        try:
            llm_instance = Llama.from_pretrained(
                repo_id="internlm/Intern-S1-mini-GGUF",
                filename="Q8_0/Intern-S1-mini-Q8_0.gguf",
                n_ctx=8192,
                n_gpu_layers=-1,
                verbose=True
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Intern-S1-mini model: {e}")

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
    """
    Uses appropriate summarization method based on loaded model.
    InternLM → chat-completion
    MedGemma → completion
    """
    global current_model_name

    base_prompt = f"""
You are SPARRC Summarizer AI, a helpful and friendly assistant for SPARRC Physiotherapy.
Your tone is professional, empathetic, and clear. Your goal is to provide beautifully formatted,
easy-to-read summaries of given content.

--- CONTENT TO SUMMARIZE ---
{chunk}
Doctor's Notes: {idea if idea else "None"}
--- END CONTENT ---

Follow SPARRC summarization guidelines. Focus on correctness, simplicity, and clarity.
"""

    try:
        # ---- InternLM (new chat API) ----
        if current_model_name == "internlm":
            prt = llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": base_prompt}
                        ]
                    }
                ],
                max_tokens=maxtokens,
                temperature=temp,
                top_p=topp,
                repeat_penalty=repeatpenalty
            )
            if "choices" in prt and len(prt["choices"]) > 0:
                return prt["choices"][0]["message"]["content"].strip()

        # ---- MedGemma (legacy completion) ----
        else:
            prt = llm.create_completion(
                prompt=base_prompt,
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
# (4) STRUCTURING FUNCTION
# ============================================================
def print_structured_summary(summary_text):
    text = summary_text.strip()
    text = re.sub(r"^(Here(?:’|'|)s a summary.*?:|Summary of .*?:)\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    sentences = re.split(r'(?<=[.!?])\s+', text)
    segmented_text = "\n".join([f"- {s.strip()}" for s in sentences if s.strip()])
    text = segmented_text

    has_bullets = bool(re.search(r"^\s*[\*\-\•]\s", text, re.MULTILINE))
    has_headings = bool(re.search(r"\*\*.*\*\*", text))
    if has_bullets or has_headings:
        formatted = "\n".join([ln.strip() for ln in text.split("\n") if ln.strip()])
        return {
            "formatted_summary": f"========== SPARRC SUMMARY ==========\n\n{formatted}\n\n===================================",
            "structured": None
        }

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

    tag_lines = []
    for section, value in structured.items():
        tag_lines.append(f"<heading>{section}</heading>")
        if isinstance(value, dict):
            for k, v in value.items():
                if v:
                    tag_lines.append(f"<point>{k}: {v}</point>")
        elif isinstance(value, list):
            for v in value:
                tag_lines.append(f"<point>{v}</point>")
        else:
            tag_lines.append(f"<point>{value}</point>")

    return {
        "formatted_summary": "\n".join(tag_lines),
        "structured": structured,
        "segmented_summary": text
    }


# ============================================================
# (5) MAIN SUMMARIZATION ENTRYPOINT
# ============================================================
def StartSummarize(path="", idea="", data="", form="false", pdf="false"):
    """
    Unified entry:
    - form/pdf = Intern-S1
    - direct data = MedGemma
    """
    if form == "true" or pdf == "true":
        ext = extract_text_from_url(path)
        images, text = ext["images"], ext["text"]
        inp = clean_summary_text(text)
        llm = get_model()  # InternLM by default

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

    if final_summary and final_summary.strip() != "":
        print_structured_summary(final_summary)
    else:
        print("[Empty Summary]")

    return final_summary
