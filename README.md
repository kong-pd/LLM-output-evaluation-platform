# LLM Output Evaluation Platform

Upload LLM responses → auto-score via LLM-as-judge → human annotation → agreement analysis → export report.

## Quick Start

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your API key
uvicorn app.main:app --reload

# In another terminal:
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000/docs | Frontend: http://localhost:5173

## MVP Features

1. **Upload** — CSV with question, context, llm_answer columns
2. **Auto evaluation** — Gemini/Grok/Claude scores each answer on faithfulness, relevance, coherence (1-5)
3. **Human annotation** — Review auto scores, agree or override
4. **Agreement analysis** — Exact match rate, per-dimension breakdown
5. **Export** — Download CSV report with auto + human scores
