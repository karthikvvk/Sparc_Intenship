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
temp = 0.4        # slightly lower for prediction consistency
topp = 0.9
repeatpenalty = 1.05

# Global cache
llm_instance = None


def get_model(model="Intern-S1-mini-Q8_0.gguf"):
    """
    Load and cache the Llama model for prediction tasks.
    """
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


def predict_chunk(chunk, llm):
    """
    Pass a chunk of cleaned data to the model with a prediction-style prompt.
    """
    prompt = f"""
You are SPARRC Prediction AI, a helpful and analytical assistant for SPARRC Physiotherapy.
Your tone is professional, empathetic, and clear.
Your goal is to carefully analyze the provided medical content and predict possible health outcomes.

--- CONTENT TO ANALYZE ---
{chunk}
--- END CONTENT ---

--- INSTRUCTIONS ---
1. **Prediction Focus:** Based ONLY on the content above, identify:
   - Potential diagnosis or condition (if medically relevant)
   - Risk level (Low, Medium, High)
   - Recommended next step or test if appropriate
2. **Faithful Reasoning:** Do NOT fabricate or assume facts not supported by the content.
3. **Clarity:** Use concise, plain language suitable for doctors and patients.
4. **Uncertainty Handling:** If the content is insufficient for a reliable prediction,
   clearly state the uncertainty instead of guessing.

--- OUTPUT ---
Provide a single, well-organized text block summarizing your predictions.
"""

    try:
        result = llm.create_completion(
            prompt=prompt,
            max_tokens=maxtokens,
            temperature=temp,
            top_p=topp,
            repeat_penalty=repeatpenalty
        )
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["text"].strip()
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
    return "[No prediction generated]"


def StartPredict(path="", data="", form="false", pdf="false"):
    """
    Main prediction entry point.
    - path: URL or file path to process
    - data: direct string input for prediction if no file
    - form/pdf flags to determine input source
    """
    if form == "true" or pdf == "true":
        ext = extract_text_from_url(path)
        images, text = ext["images"], ext["text"]

        # Clean the extracted text
        inp = clean_summary_text(text)
        llm = get_model()

        # Split into chunks for large text
        chunk_size = 5000
        chunks = [inp[i:i + chunk_size] for i in range(0, len(inp), chunk_size)]

        predictions = []
        for idx, ch in enumerate(chunks):
            prediction = predict_chunk(ch, llm)
            predictions.append(prediction)

        # Combine predictions into final output
        final_prediction = "\n".join(predictions)
    else:
        # Direct prediction mode using medgemma
        llm = get_model("medgemma-4b-it-Q4_K_M.gguf")
        try:
            result = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a medical prediction assistant."},
                    {"role": "user", "content": f"Analyze and predict possible outcomes from this data:\n{data}"}
                ],
                max_tokens=maxtokens,
                temperature=temp,
                top_p=topp,
                repeat_penalty=repeatpenalty
            )
            if "choices" in result and len(result["choices"]) > 0:
                final_prediction = result["choices"][0]["message"]["content"].strip()
            else:
                final_prediction = "[No prediction generated]"
        except Exception as e:
            print(f"[ERROR] MedGemma prediction failed: {e}")
            final_prediction = "[Error in MedGemma output]"

    return final_prediction
