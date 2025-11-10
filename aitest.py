# test_internlm.py
import time
from llama_cpp import Llama

print("[STEP 1] Initializing Intern-S1-mini-GGUF model...")

try:
    llm = Llama.from_pretrained(
        repo_id="internlm/Intern-S1-mini-GGUF",
        filename="Q8_0/Intern-S1-mini-Q8_0.gguf",
        verbose=True,
    )
    print("[STEP 2] Model loaded successfully.")
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")
    exit(1)

print("[STEP 3] Running a quick chat test...")

try:
    output = llm.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in one sentence."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
                        }
                    }
                ]
            }
        ]
    )
    print("[STEP 4] Chat response received:\n")
    print(output["choices"][0]["message"]["content"])

except Exception as e:
    print(f"[ERROR] Inference failed: {e}")

print("\n[TEST COMPLETED]")
time.sleep(1)
