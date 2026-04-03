# DataLens AI 🔍

> Upload any data. Get AI-powered insights instantly.

DataLens AI is a full-stack AI data intelligence platform 
that transforms raw data files into interactive dashboards, 
executive summaries, anomaly alerts, and actionable insights 
— in under 30 seconds.

## What It Does

- **Upload any format**: CSV, Excel, SQL, JSON, PDF, Image
- **Auto-generates**: Interactive Plotly dashboards with KPI cards
- **AI Summary**: Boardroom-ready executive paragraph
- **Key Findings**: Top 3 insights with actual numbers
- **Anomaly Detection**: Statistical outlier detection + AI explanation
- **Next Steps**: 3 actionable business recommendations
- **Q&A Panel**: Ask natural language questions about your data

## Tech Stack

**Backend**
- Python + Flask
- Pandas, NumPy, SciPy (data processing)
- PyMuPDF (PDF parsing)
- NVIDIA NIM Free APIs (AI inference)

**Frontend**
- React + Vite
- Plotly.js (interactive charts)
- TailwindCSS (styling)

**AI Models (NVIDIA NIM — all free tier)**
- Llama 3.3 70B — executive summaries & insights
- Kimi K2 — complex pattern analysis
- MiniMax M2.5 — reasoning backup
- Mistral 7B — fast formatting tasks
- Llama 3.1 8B — Q&A responses
- NV-EmbedQA — semantic search
- Llama Guard 4 — safety filtering

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in your NVIDIA NIM API keys in .env
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment Variables

Copy backend/.env.example to backend/.env and fill in:
- NVIDIA NIM API keys (get free at build.nvidia.com)
- Flask configuration

## Built By

Raghav Modi — BI Analyst & AI Systems Builder
- LinkedIn: www.linkedin.com/in/raghav-modi-a94b60228
- Email: raghavmodi2400@gmail.com

---
*Built with NVIDIA NIM free APIs. Zero paid AI costs.*
