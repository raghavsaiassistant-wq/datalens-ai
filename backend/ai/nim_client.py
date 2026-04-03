"""
nim_client.py

Production-grade client for interacting with NVIDIA NIM free APIs.
Handles multiple models, load balancing, API keys, fallback mechanisms,
and provides text generation and embedding capabilities for DataLens AI.
"""

import os
import time
import logging
from typing import Tuple, List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("NIMClient")

BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

MODELS = {
    "llama_70b": {
        "id": "meta/llama-3.3-70b-instruct",
        "key_env": "KEY_LLAMA_70B",
        "type": "text",
        "description": "Executive summary, key findings, next steps"
    },
    "kimi_k2": {
        "id": "moonshotai/kimi-k2-instruct",
        "key_env": "KEY_KIMI_K2",
        "type": "text",
        "description": "Complex pattern analysis, large datasets (1M context)"
    },
    "minimax": {
        "id": "minimaxai/minimax-m2.5",
        "key_env": "KEY_MINIMAX",
        "type": "text",
        "description": "Heavy reasoning backup, office data tasks"
    },
    "mistral_7b": {
        "id": "mistralai/mistral-7b-instruct-v0.3",
        "key_env": "KEY_MISTRAL",
        "type": "text",
        "description": "Fast tasks, column name understanding, formatting"
    },
    "llama_8b": {
        "id": "meta/llama-3.1-8b-instruct",
        "key_env": "KEY_LLAMA_8B",
        "type": "text",
        "description": "Speed-priority fallback model"
    },
    "embedqa": {
        "id": "nvidia/nv-embedqa-e5-v5",
        "key_env": "KEY_EMBEDQA",
        "type": "embed",
        "description": "Powers user Q&A on uploaded data"
    },
    "embedqa_multi": {
        "id": "nvidia/llama-3.2-nv-embedqa-1b-v2",
        "key_env": "KEY_EMBEDQA_MULTI",
        "type": "embed",
        "description": "Multilingual embeddings for GCC version"
    },
    "llama_guard": {
        "id": "meta/llama-guard-4-12b",
        "key_env": "KEY_LLAMA_GUARD",
        "type": "text",
        "description": "Input safety filtering"
    },
    "nemotron_ocr": {
        "id": "nvidia/nemotron-ocr-v1",
        "key_env": "KEY_OCR",
        "type": "vision",
        "description": "Extract text and tables from PDF and image uploads"
    },
    "page_elements": {
        "id": "nvidia/nemotron-page-elements-v3",
        "key_env": "KEY_PAGE_ELEMENTS",
        "type": "vision",
        "description": "Detect WHERE charts, tables, infographics are on a page"
    },
    "table_structure": {
        "id": "nvidia/nemoretriever-table-structure-v1",
        "key_env": "KEY_TABLE_STRUCTURE",
        "type": "vision",
        "description": "Read table rows, columns, cells → convert to Markdown"
    },
    "qwen_vl": {
        "id": "qwen/qwen3-vl",
        "key_env": "KEY_QWEN_VL",
        "type": "vision",
        "description": "Read dashboard screenshots and chart images end-to-end"
    },
}

FALLBACKS = {
    "llama_70b":     ["kimi_k2", "minimax", "mistral_7b"],
    "kimi_k2":       ["llama_70b", "minimax"],
    "minimax":       ["llama_70b", "kimi_k2"],
    "mistral_7b":    ["llama_8b"],
    "llama_8b":      ["mistral_7b"],
    "embedqa":       ["embedqa_multi"],
    "embedqa_multi": ["embedqa"],
    "llama_guard":   [],
}

class NIMClient:
    """Client for routing and managing NVIDIA NIM Model interactions."""
    
    def __init__(self) -> None:
        """
        Initializes the NIMClient, loading environment variables and model API keys.
        """
        load_dotenv()
        self._clients: Dict[str, OpenAI] = {}
        self._load_clients()
        logger.info(f"Initialized NIMClient with {len(self._clients)} active model clients.")

    def _load_clients(self) -> None:
        """
        Loads the OpenAI clients for each model using available API keys.
        """
        for model_name, config in MODELS.items():
            api_key = os.getenv(config["key_env"])
            if not api_key:
                logger.warning(f"API key missing for {model_name} (Expected in env var: {config['key_env']})")
                continue
            
            try:
                client = OpenAI(api_key=api_key, base_url=BASE_URL, timeout=45.0)
                self._clients[model_name] = client
            except Exception as e:
                logger.error(f"Failed to load client {model_name}: {str(e)[:100]}")

    def _get_client(self, model_name: str) -> Tuple[OpenAI, str]:
        """
        Gets the OpenAI client and model ID for a given model.
        """
        if model_name not in self._clients:
            raise ValueError(f"Model {model_name} is not loaded (Missing API key or initialization failed).")
        return self._clients[model_name], MODELS[model_name]["id"]

    def _strip_thinking(self, text: str) -> str:
        """
        Remove <think>...</think> blocks from model responses.
        MiniMax M2.5 and some reasoning models include thinking 
        tokens that should not be shown to users.
        """
        import re
        # Remove <think> blocks (including multiline)
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Remove any leftover <think> or </think> tags
        cleaned = re.sub(r'</?think>', '', cleaned)
        # Clean up extra whitespace
        cleaned = cleaned.strip()
        return cleaned

    def chat(self, model_name: str, user_prompt: str, system_prompt: str = "You are a helpful AI assistant.", max_tokens: int = 2048, temperature: float = 0.3) -> str:
        """
        Executes a chat completion query, automatically using fallback models on failure.
        """
        attempt_list = [model_name] + FALLBACKS.get(model_name, [])
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for current_model in attempt_list:
            try:
                client, model_id = self._get_client(current_model)
            except ValueError:
                continue

            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=messages, # type: ignore
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                latency = time.time() - start_time
                usage = response.usage
                total_tokens = usage.total_tokens if usage else 0
                
                logger.info(f"Success | Model: {current_model} | Latency: {latency:.2f}s | Tokens: {total_tokens}")
                raw = response.choices[0].message.content if response.choices[0].message.content else ""
                return self._strip_thinking(raw)
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    logger.warning(f"Rate limit (429) on {current_model}. Retrying after 10s...")
                    time.sleep(10)
                    start_time = time.time()
                    try:
                        response = client.chat.completions.create(
                            model=model_id,
                            messages=messages, # type: ignore
                            max_tokens=max_tokens,
                            temperature=temperature
                        )
                        latency = time.time() - start_time
                        usage = response.usage
                        total_tokens = usage.total_tokens if usage else 0
                        
                        logger.info(f"Success after retry | Model: {current_model} | Latency: {latency:.2f}s | Tokens: {total_tokens}")
                        raw = response.choices[0].message.content if response.choices[0].message.content else ""
                        return self._strip_thinking(raw)
                    except Exception as retry_err:
                        logger.error(f"Retry failed for {current_model}: {str(retry_err)[:100]}")
                        logger.info(f"Falling back to next model from {current_model}...")
                else:
                    logger.error(f"Error on {current_model}: {error_msg[:100]}")
                    logger.info(f"Falling back from {current_model}...")

        raise RuntimeError(f"All models in attempt chain {attempt_list} failed for request.")

    def embed(self, text: str, model_name: str = "embedqa", input_type: str = "query") -> List[float]:
        """
        Generates an embedding for the given text.
        """
        attempt_list = [model_name] + FALLBACKS.get(model_name, [])
        
        for current_model in attempt_list:
            try:
                client, model_id = self._get_client(current_model)
            except ValueError:
                continue

            start_time = time.time()
            try:
                response = client.embeddings.create(
                    model=model_id,
                    input=[text], # Expected to be an array of strings
                    extra_body={"input_type": input_type, "truncate": "END"}
                )
                latency = time.time() - start_time
                embedding = response.data[0].embedding
                
                logger.info(f"Success | Embed Model: {current_model} | Latency: {latency:.2f}s | Dimensions: {len(embedding)}")
                return embedding
            except Exception as e:
                logger.error(f"Error on {current_model} embedding: {str(e)[:100]}")
                logger.info(f"Falling back from {current_model}...")
                
        raise RuntimeError(f"All models in attempt chain {attempt_list} failed for embedding.")

    def safety_check(self, text: str) -> Dict[str, Any]:
        """
        Passes text through a safety classifier model and determines if it is safe.
        """
        try:
            result = self.chat(
                model_name="llama_guard",
                user_prompt=text,
                system_prompt="You are a content safety classifier.",
                max_tokens=20,
                temperature=0.0
            )
            is_unsafe = "unsafe" in result.lower()
            logger.info(f"Safety check completed. Safe: {not is_unsafe}")
            return {"safe": not is_unsafe, "reason": result.strip()}
        except Exception as e:
            logger.error(f"Safety check error: {str(e)[:100]}")
            return {"safe": True, "reason": "guard_unavailable"}

    def health_check(self) -> Dict[str, str]:
        """
        Pings all registered models to determine health and availability endpoints.
        """
        status: Dict[str, str] = {}
        for model_name, info in MODELS.items():
            if model_name not in self._clients:
                status[model_name] = "no_key"
            elif info["type"] == "embed":
                status[model_name] = "skipped_embed"
            else:
                try:
                    self.chat(model_name=model_name, user_prompt="Say OK", system_prompt="Just reply exactly what the user says.", max_tokens=5)
                    status[model_name] = "ok"
                except Exception as e:
                    status[model_name] = f"error: {str(e)[:50]}"
        return status

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Returns info on all registered models and whether they're loaded.
        """
        info_list = []
        for name, info in MODELS.items():
            info_list.append({
                "name": name,
                "id": info["id"],
                "type": info["type"],
                "loaded": name in self._clients,
                "description": info["description"]
            })
        return info_list
