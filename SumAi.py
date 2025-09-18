import os
from llama_cpp import Llama
from dotenv import load_dotenv
from Cleaner import clean_summary_text
from processor import extract_text_from_url  # assuming you keep the same function

# ---------- Load environment variables ----------
load_dotenv(dotenv_path="./frontend/.env")
aipath = os.getenv("AI_PATH")

# ---------- Model path (Intern-S1 only) ----------
intern_s1 = os.path.join(aipath, "Intern-S1-mini-Q8_0.gguf")
medgemma = os.path.join(aipath, "medgemma-4b-it-Q4_K_M.gguf")
# ---------- Settings ----------
maxtokens = 512
temp = 0.5
topp = 0.9
repeatpenalty = 1.05

# Global cache (single model)
llm_instance = None


def get_model(model="Intern-S1-mini-Q8_0.gguf"):
    """Always load Intern-S1 (cached)."""
    global llm_instance
    if model == "medgemma-4b-it-Q4_K_M.gguf":
        llm_instance = Llama(
            model_path=medgemma,
            n_ctx=8192,
            n_threads=os.cpu_count(),   # use all available CPU threads
            n_batch=1024,               # bigger batch → faster (tune depending on VRAM/CPU RAM)
            n_gpu_layers=-1             # use GPU acceleration fully
        )
    else:
        if not os.path.exists(intern_s1):
            raise FileNotFoundError(f"Intern-S1 model not found at {intern_s1}")
        llm_instance = Llama(
            model_path=intern_s1,
            n_ctx=8192,
            n_threads=os.cpu_count(),   # use all available CPU threads
            n_batch=1024,               # bigger batch → faster (tune depending on VRAM/CPU RAM)
            n_gpu_layers=-1             # use GPU acceleration fully
        )
    return llm_instance


def describe_images(images):
    # Placeholder for actual captioning model
    return "\n".join([f"Image {os.path.basename(img)}: MRI scan or medical page." for img in images])


def summarize_chunk(chunk, idea, llm):
    prompt = f"""
You are a medical report summarizer.
Summarize the following patient information into concise medical notes.

Patient Information:
{chunk}

Doctor's Notes: {idea if idea else "None"}
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


def StartSummarize(path="", idea="", data=""):
    print("reached summary")
    if path == "true" or path != "false":
        ext = extract_text_from_url(path)
        images, text = ext["images"], ext["text"]

        inp = clean_summary_text(text)
        print(inp)
        llm = get_model()

        print(f"\nUsing Intern-S1 (image support = {len(images) > 0})\n")

        image_text = describe_images(images) if images else ""

        # Small chunks for better summarization
        chunk_size = 5000
        chunks = [inp[i:i+chunk_size] for i in range(0, len(inp), chunk_size)]

        partial_summaries = []
        for idx, ch in enumerate(chunks):
            full_chunk = f"{ch}\n\nImage Information:\n{image_text}"
            print(f"Processing chunk {idx+1}/{len(chunks)}...")
            summary = summarize_chunk(full_chunk, idea, llm)
            partial_summaries.append(summary)

        # Merge summaries into final
        final_input = "\n".join(partial_summaries)
        final_summary = summarize_chunk(final_input, idea, llm)
    else:
        llm = get_model("medgemma-4b-it-Q4_K_M.gguf")

        # Ensure data is a string (JSON or dict)
        if isinstance(data, dict):
            prompt_input = str(data)
        else:
            prompt_input = data or "No data provided."

        print("\nUsing MedGemma (direct data mode)\n")

        try:
            prt = llm.create_completion(
                prompt=prompt_input,
                max_tokens=maxtokens,
                temperature=temp,
                top_p=topp,
                repeat_penalty=repeatpenalty
            )
            if "choices" in prt and len(prt["choices"]) > 0:
                final_summary = prt["choices"][0]["text"].strip()
            else:
                final_summary = "[No output generated]"
        except Exception as e:
            print(f"[ERROR] MedGemma summarization failed: {e}")
            final_summary = "[Error in MedGemma output]"


    print("\nFINAL SUMMARY\n")
    print(final_summary)
    return final_summary
