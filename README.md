# TrackSpendAI — AI-Powered UPI Transaction Intelligence

TrackSpendAI is a full-stack AI web application that analyses Indian UPI transaction data. The user uploads their UPI statement (PDF or CSV from PhonePe, Paytm, or any UPI app), and a multi-stage streaming pipeline runs.

## Features

- **ETL Pipeline**: Parses and normalises messy UPI data across formats.
- **Two-tier AI Categorisation**: Rule-based classifier + batched LLM calls.
- **Parallel Agent Execution**: Categorisation and Anomaly Detection Agents.
- **Dynamic RAG**: Embeds and retrieves from official Indian financial documents (SEBI, Income Tax) at query time.
- **Streaming SSE Pipeline**: Real-time progress events emitted to the React frontend.
- **Synthesis**: Final LLM report grounded in retrieved official guidance.

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion.
- **Backend**: Python 3.11, FastAPI, Pandas, Groq LLM (Llama 3.1/3.3).
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`) + Cross-Encoder re-ranking.
- **Vector Store**: In-memory (numpy-based).
- **PDF Parsing**: `pdfplumber`.

## Getting Started

### Backend Setup

1. `cd backend`
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip3 install -r requirements.txt`
5. Create `.env` with `GROQ_API_KEY`.
6. Run `python3 app/main.py`.

### Frontend Setup

1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Deployment

- **Frontend**: Vercel (configured with `vercel.json`).
- **Backend**: Render (configured with `render.yaml`).

## License

MIT
