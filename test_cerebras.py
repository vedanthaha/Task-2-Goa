import time
import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

key = os.environ["CEREBRAS_API_KEY"]
model = os.environ["CEREBRAS_MODEL"]

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}
payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": "What is artificial intelligence? Answer in 2 sentences."}
    ],
}

start = time.time()
res = requests.post("https://api.cerebras.ai/v1/chat/completions", headers=headers, json=payload)
elapsed_ms = (time.time() - start) * 1000

print(f"Status: {res.status_code}")
print(f"Total HTTP time: {elapsed_ms:.2f}ms")

data = res.json()
if "usage" in data:
    u = data["usage"]
    print(f"time_to_first_token: {u.get('time_to_first_token', 'N/A')}s")
    print(f"total_time: {u.get('total_time', 'N/A')}s")

choices = data.get("choices", [])
if choices:
    answer = choices[0].get("message", {}).get("content", "ERROR")
    print(f"Answer: {answer[:150]}")
else:
    print("ERROR response:", data)
