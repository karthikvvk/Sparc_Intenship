import os
import re
import json
from llama_cpp import Llama
from dotenv import load_dotenv
from processor import *


load_dotenv(dotenv_path="./frontend/.env")
AI_PATH = os.getenv("AI_PATH")
INTERN_PATH = os.path.join(AI_PATH, "Intern-S1-mini-Q8_0.gguf")
MEDGEMMA_PATH = os.path.join(AI_PATH, "medgemma-4b-it-Q4_K_M.gguf")
maxtokens = 512
temp = 0.5
topp = 0.9
repeatpenalty = 1.05
llm_instance = None
current_model_name = None

models = {
    "vision": None,
    "text": None
}

def load_models_once():
    global models
    
    if models["vision"] is None:
        models["vision"] = Llama(
            model_path=INTERN_PATH,
            n_ctx=8192,
            n_threads=os.cpu_count(),
            n_batch=1024,
            n_gpu_layers=0,
            verbose=False
        )

    if models["text"] is None:
        models["text"] = Llama(
            model_path=MEDGEMMA_PATH,
            n_ctx=8192,
            n_threads=os.cpu_count(),
            n_batch=1024,
            n_gpu_layers=0
        )

    return models


models = load_models_once()
vision_llm = models["vision"]
text_llm = models["text"]




def describe_image_with_internlm(image_path, vision_llm):
    try:
        ocr_text = pytesseract.image_to_string(image_path)
    except:
        ocr_text = "No OCR text extracted."

    prompt = f"""
The following text is OCR extracted from a medical image. 
Describe what the original medical image likely contained visually.

OCR TEXT:
{ocr_text}

IMAGE DESCRIPTION:"""

    out = vision_llm.create_completion(
        prompt=prompt,
        max_tokens=256,
        temperature=0.3
    )
    return out["choices"][0]["text"].strip()



def summarize_with_medgemma(llm, text, idea):
    prompt = f"""
You are SPARRC Summarizer AI, a helpful and friendly assistant for SPARRC Physiotherapy.
Your tone is professional, empathetic, and clear. Your goal is to provide beautifully formatted,
easy-to-read summaries of given content.

--- CONTENT TO SUMMARIZE ---
{text}
Doctor's Notes: {idea if idea else "None"}
--- END CONTENT ---

Follow SPARRC summarization guidelines. Focus on correctness, simplicity, and clarity.
"""
    # print(prompt)
    prt = llm.create_completion(
        prompt=prompt,
        max_tokens=maxtokens,
        temperature=temp,
        top_p=topp,
        repeat_penalty=repeatpenalty
    )
    # print(prt)
    return prt["choices"][0]["text"].strip()



def predict_with_medgemma(llm, text):
    prompt = f"""
You are SPARRC Prediction AI, a helpful and analytical assistant for SPARRC Physiotherapy.
Your tone is professional, empathetic, and clear.
Your goal is to carefully analyze the provided medical content and predict possible health outcomes.

--- CONTENT TO ANALYZE ---
{text}
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

    prt = llm.create_chat_completion(
        prompt=prompt,
        max_tokens=maxtokens,
        temperature=temp,
        top_p=topp,
        repeat_penalty=repeatpenalty
    )

    return prt["choices"][0]["text"].strip()


def StartPrediction(path="", data="", form="false", pdf="false"):
    if form == "true" or pdf == "true":
        ext = extract_text_from_url(path)
        text = clean_summary_text(ext["text"])
        images = ext["images"]
    else:
        text = clean_summary_text(str(data))
        images = []

    if images:
        notes = []
        for img in images:
            notes.append(describe_image_with_internlm(img, vision_llm))
        text = text + "\n\nImage Notes:\n" + "\n".join(notes)

    prediction = predict_with_medgemma(text_llm, text)
    prediction = clean_summary_text(prediction)
    dropped = droper(prediction)
    stpred = print_structured_summary(dropped)
    return stpred



def StartSummarize(path="", idea="", data="", form="false", pdf="false"):

    ext = extract_text_from_url(path) if (form=="true" or pdf=="true") else None
    if ext:
        images = ext["images"]
        text = clean_summary_text(ext["text"])
    else:
        text = clean_summary_text(str(data))
        images = []

    if images:
        notes = []
        for img in images:
            notes.append(describe_image_with_internlm(img, vision_llm))
        text = text + "\n\nImage Notes:\n" + "\n".join(notes)


    summary_raw = summarize_with_medgemma(text_llm, text, idea)
    # summary_raw = """SUMMARY RAW: Here's a summary of the patient information: Anandan Kumar, a 41 year old male IT professional with a 5 year history of chronic low back pain, presents with a confirmed L4 L5 disc bulge based on MRI. He experiences bilateral dull ache and occasional sharpness in his lumbar spine, exacerbated by prolonged sitting and bending forward. This leads to numbness in the left leg, difficulty tying shoelaces, and pain radiating down the leg after 1km. His symptoms are aggravated by a 25km daily commute in a car with mixed road conditions. He has used a new office chair and is currently using an ergonomic chair, but still experiences pain that impacts his productivity and sleep. He reports stiffness in the morning and slouched posture. He has a history of physiotherapy 2 years ago providing temporary relief. He uses occasional painkillers and is currently not engaging in any specific treatment. His medical history includes a previous MRI showing L4 L5 disc bulge, and he is currently using a foam mat for seating. json { patient name: Anandan Kumar, age: 41, gender: Male, occupation: IT Professional, chief complaint: Chronic low back pain, duration: 5 years, diagnosis: L4 L5 disc bulge, severity: Chronic, location: Lumbar Spine L4 L5, pain characteristics: Bilateral dull ache with occasional sharpness, aggravating factors: [ Prolonged sitting, Bending forward ], alleviating factors: [ Resting ], associated symptoms: [ Numbness in left leg, Difficulty tying shoelaces, Pain radiating down the leg after 1km, Stiff in the morning, Slouched posture, Reduced productivity at work, Disturbed due to pain ], medications: [ Occasional painkiller ], treatment history: [ Physiotherapy 2 years ago (temporary relief), Started using a new office chair, Ergonomic Chair,"""
    summary_raw = clean_summary_text(summary_raw)
    # print("SUMMARY RAW:", summary_raw)
    dropped = droper(summary_raw)
    print("DROPPED:", dropped)
    stsum = print_structured_summary(dropped)
    # stsum = {
    #     "formatted_summary": "<h2>Summary</h2>\n<ul>\n<li>The output of this patient's data is a summary of their patient information, including their name, age, gender, occupation, chief complaint, diagnosis, severity, location, pain characteristics, aggravating factors, alleviating factors, associated symptoms, and medications.</li>\n<li>The summary is as follows:\n\nPatient Name: Anandan Kumar\n\nPatient Gender: Male\n\nPatient Occupation: IT Professional\n\nChief Complaint: Chronic low back pain\n\nDuration: 5 years\n\nDiagnosis: L4 L5 disc bulge\n\nSeverity: Chronic\n\nLocation: Lumbar Spine L4 L5\n\nPain Characteristics: Bilateral dull ache and occasional sharpness\n\nAggravating Factors: [Prolonged sitting, Bending forward]\n\nAlleviating Factors: [Resting]\n\nAssociated Symptoms: [Numbness in left leg, Difficulty tying shoelaces, Pain radiating down the leg after 1km]\n\nMedications: [Occasional painkiller]\n\nMedications: [Started using a new office chair, Ergonomic Chair]\n\nThe summary highlights the patient's medical history, including the MRI that revealed their L4 L5 disc bulge, the severity of their pain, the location of their pain, and the associated symptoms, including numbness in their left leg.</li>\n<li>The summary also includes the patient's medications and their use, which highlights the patient's ongoing treatment.</li>\n<li>Overall, this summary provides an overview of the patient's patient information and their medical history, which can be used to better understand their medical condition and to guide their treatment plan.</li>\n</ul>",
    #     "structured": None
    # }
    return stsum
