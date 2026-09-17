# LLM Output Evaluation Platform

A tool for answering the question: **"Are these LLM responses actually good?"**

I built this because I realized after doing [golden-set eval in GreenCheck](https://github.com/kong-pd/greenwashing-detector) that there wasn't a clean, lightweight way to batch-evaluate LLM outputs with both automated scoring and human review. Every tool I found was either enterprise-grade overkill or a Jupyter notebook someone abandoned.

## What it does

You upload a CSV of LLM-generated responses. The system auto-scores each one on three dimensions (faithfulness, relevance, coherence) using LLM-as-judge. Then you can go through the results, agree or override the auto scores, and the system tracks how often humans and the auto-scorer agree. At the end you export a report.

That's it. No model training, no fine-tuning, no ML pipeline. It's a quality inspection tool that happens to use an LLM as the inspector.

## Architecture decisions and why

**SQLite instead of PostgreSQL** — for an MVP this removes an entire infrastructure dependency. The data model uses SQLAlchemy ORM so switching to Postgres later is a one-line change.

**LLM-as-judge with rubric prompts** — instead of training a scoring model (which needs labeled data I don't have), I give the judge LLM a structured rubric with explicit 1-5 criteria. The rubric is domain-agnostic — faithfulness just checks whether the answer matches the provided context, regardless of whether the context is about medicine or customer support.

**Gemini → Grok → Claude fallback chain** — free-tier APIs have rate limits and outages. The system tries providers in order and falls back automatically. Gemini Lite handles most requests within the free quota.

**BackgroundTasks over Celery** — FastAPI's built-in BackgroundTasks is plenty for MVP-scale. No Redis, no message broker, no extra infrastructure. The frontend polls every 3 seconds to show progress.

**Three scoring dimensions** — faithfulness (does it match the source?), relevance (does it answer the question?), coherence (is it well-written?). These are the standard dimensions from LLM evaluation literature and they work across domains because the context column carries the domain knowledge.

## How to run

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env        # add at least GEMINI_API_KEY
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Upload `backend/tests/sample_data.csv` to see it work.

Get a free Gemini API key at https://aistudio.google.com/apikey.

## What the CSV looks like

```csv
question,context,llm_answer
What are your hours?,Open Mon-Fri 9-6. Weekend email only.,We're open 24/7!
```

- `question` — what was asked
- `context` — the source of truth (optional but needed for faithfulness scoring)
- `llm_answer` — what the LLM responded

The system also accepts `answer`, `response`, `output` as column name aliases.

## What's not great

**No retry for failed items.** If Gemini rate-limits mid-batch, those items stay as "error". You'd have to re-upload. A retry button is the obvious next feature.

**Agreement metrics are basic.** I'm using exact match rate and ±1 tolerance. Cohen's Kappa would be more statistically rigorous for measuring inter-rater reliability, but for an MVP the simple metrics tell you enough.

**Single annotator.** There's no user system — anyone who opens the UI can annotate. Multi-annotator support with inter-annotator agreement would make this more credible for actual research use.

**No caching on LLM calls.** Re-uploading the same CSV scores everything from scratch. Could hash the inputs and skip already-scored items.

## Stack

FastAPI · SQLAlchemy · SQLite · React · Vite · Gemini/Grok/Claude APIs

## What I learned

This was my first data-oriented project. The biggest lesson was that the hard part isn't the ML — it's designing evaluation criteria that are consistent and meaningful, and building the pipeline so it doesn't block the UI while processing. The LLM-as-judge approach is surprisingly effective when you give it a clear rubric, but the rubric design matters more than the model choice.
