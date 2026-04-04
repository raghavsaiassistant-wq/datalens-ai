"""
image_parser.py

Parses data from images, charts, and dashboards using visual language models.
"""
import time
import base64
import json
import io
import pandas as pd
from PIL import Image
from parsers.base_parser import BaseParser, DataProfile
from utils.data_profiler import DataProfiler

class ImageParser(BaseParser):
    def parse(self, file_path: str, file_name: str, nim_client=None) -> DataProfile:
        start_time = time.time()
        warnings = []
        
        self._validate_file(file_path, ['.png', '.jpg', '.jpeg', '.webp'])
        
        if not nim_client:
            raise ValueError("NIMClient required for ImageParser.")
            
        # STEP 1: Image Preprocessing
        img = Image.open(file_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        w, h = img.size
        if w > 2000 or h > 2000:
            ratio = min(2000.0/w, 2000.0/h)
            new_size = (int(w*ratio), int(h*ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # STEP 2 & 3: Qwen VLM analysis
        prompt = """Analyze this data visualization or dashboard image.
Extract ALL numerical data you can see.
Identify: chart type, axis labels, data values, titles, legends.
Return your response in this EXACT JSON format:
{
  "chart_type": "bar|line|pie|table|dashboard|other",
  "title": "chart title if visible",
  "columns": ["col1", "col2"],
  "data": [{"col1": val, "col2": val}],
  "summary": "one sentence describing what this shows",
  "x_axis_label": "label or null",
  "y_axis_label": "label or null"
}
Return ONLY valid JSON."""

        df = pd.DataFrame()
        summary_text = ""
        
        try:
            resp = self._call_vision_nim(nim_client, "qwen_vl", image_b64, prompt)
            resp = nim_client._strip_thinking(resp)
            resp = resp.replace("```json", "").replace("```", "").strip()
            
            parsed = json.loads(resp)
            
            if "data" in parsed and "columns" in parsed:
                df = pd.DataFrame(parsed["data"], columns=parsed["columns"])
                summary_text = parsed.get("summary", "")
        except Exception as e:
            warnings.append(f"First VLM pass failed: {e}. Retrying CSV prompt.")
            try:
                resp2 = self._call_vision_nim(nim_client, "qwen_vl", image_b64, "Extract tabular data to standard JSON format [{col:val}]. ONLY JSON.")
                resp2 = nim_client._strip_thinking(resp2)
                resp2 = resp2.replace("```json", "").replace("```", "").strip()
                parsed2 = json.loads(resp2)
                df = pd.DataFrame(parsed2)
            except Exception as e2:
                df = pd.DataFrame({"extracted_text": [str(e2)]})
                warnings.append("Complete structured extraction failed. Returned raw extract.")
                
        if df.empty:
            df = pd.DataFrame({"extracted_text": ["No data found"]})
            
        processing_time = round(time.time() - start_time, 2)
        profile = DataProfiler.profile(df, "image", file_name, processing_time, warnings)
        
        if summary_text:
            profile.text_content = f"VLM SUMMARY: {summary_text}\n\n" + profile.text_content
            
        return profile
        
    def _call_vision_nim(self, nim_client, model_name, image_b64, prompt):
        from ai.nim_client import MODELS
        client = nim_client._clients.get(model_name)
        if client is None:
            raise ValueError(f"Vision model '{model_name}' is not loaded. Ensure {MODELS[model_name]['key_env']} is set in your .env file.")
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                {"type": "text", "text": prompt}
            ]
        }]
        resp = client.chat.completions.create(
            model=MODELS[model_name]["id"],
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
            timeout=45
        )
        return resp.choices[0].message.content
