# LLM Output Evaluation Platform

This is a tool for evaluating LLM-generated responses. You can upload a dataset of question-answer pairs, get automatic quality scores via LLM-as-judge, layer on human annotation, then see how well the two agree.

I built this to explore a question that comes up a lot in LLM development: when you use one model to judge another model's output, how much can you trust the scores? The human annotation layer lets you find out. You review the auto-generated scores, agree or override them, and the platform tracks agreement rates across dimensions.

## How It Works

1. **Upload** a CSV with `question`, `context`, and `llm_answer` columns.
2. The backend sends each row to an LLM judge (Gemini → Groq → Claude fallback chain) and scores it on three dimensions: faithfulness, relevance, and coherence (1–5 scale).
3. Open the **annotation UI** to review each score — agree with it, or override with your own.
4. The **dashboard** shows agreement analysis: exact match rate, per-dimension breakdown, score distributions.
5. **Export** everything as a CSV report with both auto and human scores.

## Setup

```bash
# backend
cd backend
pip install -r requirements.txt
cp .env.example .env          # add your API key(s)
uvicorn app.main:app --reload # localhost:8000

# frontend
cd frontend
npm install
npm run dev                   # localhost:5173
```

API docs at http://localhost:8000/docs

## Stack

**Backend:** Python · FastAPI · SQLAlchemy · SQLite

**Frontend:** React · Vite · Axios · Recharts

**Evaluation:** LLM-as-judge with multi-model fallback (Gemini → Groq → Claude)

## License

MIT