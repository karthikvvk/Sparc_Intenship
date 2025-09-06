import time, os, requests
from llama_cpp import Llama
from processor import *
from dotenv import load_dotenv
from Cleaner import *
# ---------- Load environment variables ----------
load_dotenv(dotenv_path="./frontend/.env")
aipath = os.getenv("AI_PATH")

# ---------- Model paths ----------
lis = [
    "/medgemma-4b-it-Q4_K_M.gguf",
    "/gpt-oss-20b-MXFP4.gguf"
]

# ---------- Select available model ----------
for i in lis:
    if i.startswith("http"):
        try:
            r = requests.head(i, allow_redirects=True, timeout=5)
            if r.status_code == 200:
                model = i
                break
        except:
            continue
    elif os.path.exists(aipath + i):
        model = aipath + i
        break
else:
    raise Exception("Model not found. Place the model file correctly.")

model_name = model.split("/")[-1].split(".")[0]

# ---------- Settings ----------
space = "\n\n\n\n\n\n"
maxtokens = 512        # allow bigger summaries
temp = 0.7
topp = 0.9
repeatpenalty = 1.05

print("Using model:", model)

# ---------- Initialize Llama ----------
llm = Llama(
    model_path=model,
    n_ctx=8192,                   # larger context for big PDFs
    n_threads=os.cpu_count(),
    n_batch=512,                  # speed up processing
    n_gpu_layers=-1               # use GPU if available
)

print(space, "\nmodel_name:", model_name, "\nmaxtokens:", maxtokens, "\ntopp:", topp,
          "\nrepeatpenalty:", repeatpenalty, "\ntemp:", temp,model, space)


# def StartSummarize(path, idea=""):
#     print(space, "\nmodel_name:", model_name, "\nmaxtokens:", maxtokens, "\ntopp:", topp,
#           "\nrepeatpenalty:", repeatpenalty, "\ntemp:", temp, space)

#     raw_text, file_ext = extract_text_from_url(path)
#     inp = clean_summary_text(raw_text)
    
#     prompt = f"""
# write a neet summary about this patient.
# Patient Information:
# {inp}

# Doctor's Notes: {idea if idea else "None"}
# """
#     print(prompt)
#     prt = llm.create_chat_completion(
#         messages=[
#             {"role": "system", "content": "You are a medical report summarizer."},
#             {"role": "user", "content": prompt},
#         ],
#         max_tokens=maxtokens,
#         temperature=temp,
#         top_p=topp,
#         repeat_penalty=repeatpenalty,
#     )

#     print(space + "RAW OUTPUT" + space)
#     print(prt)

#     print(space + "OUTPUT" + space)

#     # --- handle both formats (chat vs. text models) ---
#     if "message" in prt["choices"][0]:
#         output = prt["choices"][0]["message"]["content"].strip()
#     else:
#         output = prt["choices"][0]["text"].strip()

#     print(output + space)
#     return output





def summarize_chunk(chunk, idea=""):
    """Summarize one chunk of text to avoid context overflow."""
    prompt = f"""
Summarize the following patient information into concise medical notes.

Patient Information:
{chunk}

Doctor's Notes: {idea if idea else "None"}
"""
    prt = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "You are a medical report summarizer."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=maxtokens,
        temperature=temp,
        top_p=topp,
        repeat_penalty=repeatpenalty,
        stream=False
    )

    if "message" in prt["choices"][0]:
        return prt["choices"][0]["message"]["content"].strip()
    return prt["choices"][0]["text"].strip()


def StartSummarize(path, idea=""):
    raw_text, file_ext = extract_text_from_url(path)
    inp = clean_summary_text(raw_text)

    # --- chunking large input ---
    chunk_size = 2000  # tokens approx
    chunks = [inp[i:i+chunk_size] for i in range(0, len(inp), chunk_size)]

    partial_summaries = []
    for idx, ch in enumerate(chunks):
        print(f"Processing chunk {idx+1}/{len(chunks)}...")
        partial_summaries.append(summarize_chunk(ch, idea))

    # --- final merge summary ---
    final_input = "\n".join(partial_summaries)
    final_summary = summarize_chunk(final_input, idea)

    print(space + "FINAL SUMMARY" + space)
    print(final_summary + space)
    return final_summary