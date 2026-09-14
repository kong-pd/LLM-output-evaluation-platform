# LLM Output Evaluation Platform

Upload LLM-generated responses, auto-score them via LLM-as-judge, review with human annotation, export evaluation reports.

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in at least one API key
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Backend API: http://localhost:8000/docs
Frontend: http://localhost:5173

## Run Tests

```bash
cd backend
python -m pytest tests/ -v

# With real API:
GEMINI_API_KEY=... python -m pytest tests/ -v -k integration
```

## MVP Roadmap

- [x] Step 1: Data layer + CSV upload API
- [x] Step 2: Auto evaluation engine (LLM-as-judge with Gemini/Grok/Claude fallback)
- [x] Step 3: Frontend dashboard + annotation UI
- [ ] Step 4: Human vs auto agreement analysis
- [ ] Step 5: Export evaluation reports

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Auto Eval:** Gemini → Grok → Claude fallback chain
- **Frontend:** React + Vite
