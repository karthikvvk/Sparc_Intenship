import os
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


def get_model(model="Intern-S1-mini-Q8_0.gguf"):# Default to internlm
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
        #use medgemma
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
You are SPARRC Summarizer AI, a helpful and friendly assistant for SPARRC Physiotherapy. Your tone is professional, empathetic, and clear. Your goal is to provide beautifully formatted, easy-to-read **summaries** of given content.

--- CONTENT TO SUMMARIZE ---
{chunk}
Doctor's Notes: {idea if idea else "None"}
--- END CONTENT ---

--- INSTRUCTION ---
1. **Summarize Faithfully:** Summarize ONLY the content provided above. Do not add new facts or assumptions.
2. **Summarization Style:**  
    - Use **simple, clear language** so that anyone can understand.  
    - Highlight only the **most important points** in the text.  
3. **Handle Unknowns Politely:** If the input is empty or unclear, respond with:  
    "I'm sorry, I couldn't find enough information to summarize right now. 😔"  
4. **Handle Distress or Emotional Content:** If the content expresses sadness, distress, or self-harm thoughts, summarize carefully and add an empathetic note at the end suggesting professional help.
5. **SPARRC Focus:** If the text contains both SPARRC and non-SPARRC info, focus mainly on **SPARRC-related** parts while briefly noting other parts if necessary.
6. **Formatting:** Use bullet points and headings to make the summary easy to read.
7. **Doctor's Notes:** The doctor's POV has to supported with claims if related information is correctly mentioned. Else just supress this.
8. **sanitization:** Dont include any of the words mentions from INSTRUCTIONS. These are for you to help design perferct summary.
"""
    
    try:
        #calling the model for actual summary prompt
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


def StartSummarize(path="", idea="", data="", form="false", pdf="false"):
    if form == "true" or pdf == "true":
        ext = extract_text_from_url(path)
        images, text = ext["images"], ext["text"]# Extracted text and images

        inp = clean_summary_text(text)# Cleaned text for summarization
        llm = get_model()

        # print(f"\nUsing Intern-S1 (image support = {len(images) > 0})\n")#outputs the models being used

        image_text = describe_images(images) if images else ""

        # Small chunks for better summarization
        chunk_size = 5000
        chunks = [inp[i:i+chunk_size] for i in range(0, len(inp), chunk_size)]

        partial_summaries = []
        for idx, ch in enumerate(chunks):
            full_chunk = f"{ch}\n\nImage Information:\n{image_text}"
            # print(f"Processing chunk {idx+1}/{len(chunks)}...")# chunking progress display
            summary = summarize_chunk(full_chunk, idea, llm)
            partial_summaries.append(summary)

        # Combine chunked summaries into final
        final_input = "\n".join(partial_summaries)
        final_summary = summarize_chunk(final_input, idea, llm)
    else:
        
        llm = get_model("medgemma-4b-it-Q4_K_M.gguf")
        print(f"\nUsing MedGemma (direct data mode)\n")

        # # Ensure data is a string
        # if isinstance(data, dict):
        #     data = str(data)

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


    # print("\nFINAL SUMMARY\n")
    # print(final_summary)
    return final_summary
