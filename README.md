# LLM Output Evaluation Platform

Upload LLM responses → auto-score via LLM-as-judge → human annotation → evaluation reports.

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
