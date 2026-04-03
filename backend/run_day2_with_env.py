import os
import sys
sys.path.insert(0, r"d:\Datalens.ai")
from test_nvidia_keys import MODELS

for model in MODELS:
    if "Llama 3.3 70B" in model["name"]: os.environ["KEY_LLAMA_70B"] = model["api_key"]
    if "Kimi K2" in model["name"]: os.environ["KEY_KIMI_K2"] = model["api_key"]
    if "MiniMax" in model["name"]: os.environ["KEY_MINIMAX"] = model["api_key"]
    if "Mistral 7B" in model["name"]: os.environ["KEY_MISTRAL"] = model["api_key"]
    if "Llama 3.1 8B" in model["name"]: os.environ["KEY_LLAMA_8B"] = model["api_key"]
    if "EmbedQA" in model["name"] and "Multilingual" not in model["name"]: os.environ["KEY_EMBEDQA"] = model["api_key"]
    if "Multilingual" in model["name"]: os.environ["KEY_EMBEDQA_MULTI"] = model["api_key"]
    if "Llama Guard" in model["name"]: os.environ["KEY_LLAMA_GUARD"] = model["api_key"]

import subprocess
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'
result = subprocess.run([sys.executable, "test_day2.py"], env=env, capture_output=True, text=True, encoding='utf-8')
with open("day2_out.txt", "w", encoding="utf-8") as f: f.write(result.stdout)
with open("day2_err.txt", "w", encoding="utf-8") as f: f.write(result.stderr)
