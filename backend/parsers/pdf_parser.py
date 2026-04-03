"""
pdf_parser.py

Parses tabular data and text from PDFs. Detects tables with PyMuPDF, 
falling back to NIM Vision OCR if no tables are found.
"""
import fitz # PyMuPDF
import pandas as pd
import re
import time
import base64
import json
from parsers.base_parser import BaseParser, DataProfile
from utils.data_profiler import DataProfiler

class PDFParser(BaseParser):
    def parse(self, file_path: str, file_name: str, nim_client=None) -> DataProfile:
        start_time = time.time()
        warnings = []
        
        self._validate_file(file_path, ['.pdf'])
        
        doc = fitz.open(file_path)
        total_pages = len(doc)
        
        all_tables_dfs = []
        all_text = ""
        
        for i in range(total_pages):
            page = doc[i]
            
            # STAGE 1A: Text extraction
            text = page.get_text()
            text = re.sub(r'\s+', ' ', text)
            all_text += text + "\n"
            
            # STAGE 1B: Table detection
            if hasattr(page, "find_tables"):
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for tab in tabs.tables:
                        df_tab = tab.to_pandas()
                        if not df_tab.empty and len(df_tab.columns) > 1:
                            all_tables_dfs.append(df_tab)
                            
        df = pd.DataFrame()
        
        if all_tables_dfs:
            df = max(all_tables_dfs, key=len)
            warnings.append(f"Found {len(all_tables_dfs)} tables across {total_pages} pages. Using largest.")
        else:
            # STAGE 2: OCR with NIM
            if nim_client and len(all_text.strip()) < 100:
                warnings.append("No tables found. Attempting vision OCR via NIM.")
                
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("jpeg")
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                
                prompt = "Extract tabular data from this image. Return strictly as JSON with a 'columns' list and 'data' list of row arrays. No markdown."
                try:
                    resp = self._call_vision_nim(nim_client, b64_img, prompt)
                    resp = nim_client._strip_thinking(resp)
                    resp = resp.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(resp)
                    if "columns" in parsed and "data" in parsed:
                        df = pd.DataFrame(parsed["data"], columns=parsed["columns"])
                except Exception as e:
                    warnings.append(f"Vision OCR failed: {e}")
                    
            if df.empty and not nim_client and len(all_text.strip()) < 100:
                raise ValueError("PDF has no extractable tables. Provide nim_client for OCR.")
                
            # TEXT-ONLY Fallback
            if df.empty:
                warnings.append("No tabular data found. Text content extracted.")
                df = pd.DataFrame({"text_content": [all_text[:5000]]})
                
        doc.close()
        
        if not df.empty and "text_content" not in df.columns:
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            
        processing_time = round(time.time() - start_time, 2)
        profile = DataProfiler.profile(df, "pdf", file_name, processing_time, warnings)
        
        # STAGE 3: Merge rich text
        if len(all_text) > 100 and "text_content" not in df.columns:
            profile.text_content = f"CONTEXT TEXT: {all_text[:1000]}...\n\n" + profile.text_content
            
        return profile
        
    def _call_vision_nim(self, nim_client, image_b64, prompt):
        model_name = "nemotron_ocr" 
        try:
            client = nim_client._clients[model_name]
        except KeyError:
             client = nim_client._clients["qwen_vl"]
             model_name = "qwen_vl"
             
        from ai.nim_client import MODELS
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
        resp = client.chat.completions.create(
            model=MODELS[model_name]["id"],
            messages=messages,
            temperature=0.0,
            max_tokens=1000,
            timeout=45
        )
        return resp.choices[0].message.content
