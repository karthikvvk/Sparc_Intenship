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
    "/medgemma-4b-it-GGUF/medgemma-4b-it-Q4_K_M.gguf",
    "/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf",
    "https://drive.google.com/file/d/17JRpjf_32DRLsOLzP9fWiiuIpl4drtH9/view?usp=sharing"
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
maxtokens = 256        # Reduced for faster inference
temp = 0.7
topp = 0.9
repeatpenalty = 1.1

# ---------- Initialize Llama ----------
llm = Llama(
    model_path=model,
    n_ctx=1024,                   # Reduced for speed
    n_threads=os.cpu_count(),
    n_batch=128

)


print(space, "\nmodel_name:", model_name, "\nmaxtokens:", maxtokens, "\ntopp:", topp,
          "\nrepeatpenalty:", repeatpenalty, "\ntemp:", temp,model, space)



# ---------- Summarize Function ----------
def StartSummarize(path, idea=""):
    print(space, "\nmodel_name:", model_name, "\nmaxtokens:", maxtokens, "\ntopp:", topp,
          "\nrepeatpenalty:", repeatpenalty, "\ntemp:", temp, space)

    raw_text, file_ext = extract_text_from_url(path)
    inp = clean_summary_text(raw_text)

    
    prompt = f"""
write a neet summary about this patient.
Patient Information:
{inp}

Doctor's Notes: {idea if idea else "None"}
"""
    

    print(space, model, space)
    print(space, prompt, space)

    prt = llm(
        prompt=prompt,
        max_tokens=maxtokens,
        temperature=temp,
        top_p=topp,
        repeat_penalty=repeatpenalty,
    )

    print(space + "RAW OUTPUT" + space)
    print(prt)

    print(space + "OUTPUT" + space)
    output = prt["choices"][0]["text"].strip()
    print(output + space)
    return output
