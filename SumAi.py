import time
from llama_cpp import Llama
from processor import *




model = "/home/muruga/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf"
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



def StartSummarize(path):
    print(space, "\nmodel_name:", model_name, "\nmaxtokens:", maxtokens, "\ntopp:", topp, "\nrepeatpenalty:", repeatpenalty, "\ntemp:" , temp ,space)


    inp = extract_text_from_url(path)

    prompt = f"""
    You are a medical summarizer specialized in clinical documentation.
    Given the structured patient details below in JSON format, generate a single concise medical introduction paragraph. 

    The summary must:
    - Be strictly in one paragraph (no points or lists).
    - Include demographics (name, age, gender, occupation, lifestyle).
    - Mention chief complaints, duration, pain characteristics, associated symptoms.
    - Integrate relevant medical history, current medications, past treatments, and investigation reports.
    - Highlight aggravating/relieving factors, movement restrictions, sleep/ergonomic habits, and lifestyle contributors.
    - Use correct medical terminology and keep tone professional, crisp, and factual.
    - Avoid meta commentary, disclaimers, or repeating instructions.

    Patient Details:
    {inp}
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