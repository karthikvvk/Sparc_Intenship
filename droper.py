# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v0.6")
messages = [
    {"role": "user", "content": f"""
You are a droping + cleaner model. so remove any thought process or the reasoning steps from the input and provide only the final structured data output.
make sure whole detail is covered.
structure output point wise.
output should be smaller than the input.
so dont include any of your though process and remove any such from the input.


input:{'hi'}
"""},
]
print(pipe(messages))