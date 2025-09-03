import time, os
from llama_cpp import Llama
from processor import *



lis = ["/home/muruga/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf", "./gpt-oss-20b-MXFP4.gguf", "https://drive.google.com/file/d/17JRpjf_32DRLsOLzP9fWiiuIpl4drtH9/view?usp=sharing"]
for i in lis:
    if i.startswith("http"):
        r = requests.head(i, allow_redirects=True, timeout=5)
        if r.status_code == 200:
            model = i
            break
    elif os.path.exists(i):
        model = i
        break
    else:
        Exception("Model not found. Place model in './gpt-oss-20b-MXFP4.gguf' current dir")


model_name = model.split("/")[-1].split(".")[0]
space = "\n\n\n\n\n\n"
maxtokens=512
temp=0.7
topp=0.9
repeatpenalty=1.1

llm = Llama(
    model_path=model,
    n_ctx=2048
)



def StartSummarize(path, idea=""):
    print(space, "\nmodel_name:", model_name, "\nmaxtokens:", maxtokens, "\ntopp:", topp, "\nrepeatpenalty:", repeatpenalty, "\ntemp:" , temp ,space)
    inp = extract_text_from_url(path)


    prompt = f"""
    You are a medical summarizer specializing in clinical documentation. Using the structured patient details provided in JSON, write a single, concise medical introduction paragraph that:  

    - Integrates demographics (name, age, gender, occupation, lifestyle), chief complaints with duration and pain characteristics, associated symptoms, relevant medical history, current medications, past treatments, and investigation findings.  
    - Includes aggravating/relieving factors, movement restrictions, sleep/ergonomic habits, and lifestyle contributors if present.  
    - Maintains a professional, factual, and medically accurate tone without bullet points, meta commentary, or instructions.  

    Patient Details: {inp}  
    Doctor's Additional Thoughts: {idea if idea else "N/A"}  
    """


    print(space, prompt, space)


    prt = llm(
    prompt,
    max_tokens=maxtokens,
    temperature=temp,
    top_p=topp,
    repeat_penalty=repeatpenalty
    )


    print(space + "RAW OUTPUT" + space)
    print(prt)
    print(space + "OUTPUT" + space)
    print(prt["choices"][0]["text"]+ space)
    refined = (prt["choices"][0]["text"]+ space)
    return refined
