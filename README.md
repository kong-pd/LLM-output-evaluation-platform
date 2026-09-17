# LLM Output Evaluation Platform

A tool for evaluating LLM-generated responses — with extra support for RAG pipelines. Upload a dataset of question-answer pairs, get automatic quality scores via LLM-as-judge, layer on human annotation, then see how well the two agree. When scores are low, the platform classifies what went wrong and points at the pipeline stage responsible.

I built this to explore a question that comes up a lot in LLM development: when you use one model to judge another model's output, how much can you trust the scores? The human annotation layer lets you find out — you review the auto-generated scores, agree or override them, and the platform computes Cohen's Kappa to quantify agreement. The RAG-specific dimensions (context relevance, groundedness) and root cause analysis were my first attempt at going beyond "the answer is bad" toward "here's why, and which part of the pipeline to fix."

## How It Works

1. **Upload** a CSV with `question`, `context`, and `llm_answer` columns.
2. The backend sends each row to an LLM judge (Gemini → Groq → Claude fallback chain) and scores it on up to five dimensions (1–5 scale):
   - **All rows:** faithfulness, relevance, coherence
   - **Rows with context:** also context relevance (rates the retriever) and groundedness (does the answer actually use the context?)
   - Low-scoring items get an automatic error classification — hallucination, contradiction, incomplete, off-topic, or poor reasoning.
3. Open the **annotation UI** to review each score — agree with it, or override with your own.
4. The **analysis panels** show:
   - **Agreement:** exact match rate, ±1 match rate, Cohen's Kappa (overall and per-dimension), confusion matrix
   - **Root cause analysis:** error type breakdown, average scores per dimension, pipeline diagnosis (tells you whether the retriever or generator is the likely problem)
   - **Difficulty ranking:** items sorted by average score, tagged hard/medium/easy with their weakest dimension
5. **Export** everything as a CSV report with auto scores, human scores, and error types.

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

**Frontend:** React · Vite · React Router

**Evaluation:** LLM-as-judge with multi-model fallback (Gemini → Groq → Claude)

## License

MIT
