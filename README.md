# Evidence Ledger

**A multi-agent due diligence verification platform for startup data rooms.**

Upload a startup's pitch deck and supporting documents. Evidence Ledger extracts every metric and claim with its exact source page, reconciles figures across documents, flags contradictions and unsupported assertions, and lets you interrogate the findings through a citation-grounded chat or a downloadable PDF report.

> **Evidence, not verdicts.** The system never outputs an investment recommendation or a single risk score. It surfaces what is consistent, what contradicts, and what is asserted without support, and leaves the judgment to you.

---

## The problem

Evaluating a data room means manually cross-referencing numbers and claims across a pitch deck, financial statements, and cap tables. Generic RAG chatbots can retrieve a passage from one document, but they don't reconcile figures across sources, don't flag claims that nothing backs up, and don't apply transparent risk criteria. Evidence Ledger treats due diligence as a **verification** problem rather than a retrieval problem.

## Features

- **Structured extraction.** PDF parsing with an OCR fallback for scanned pages. Every metric and claim is stored with its source file, page number, and verbatim sentence.
- **Deterministic normalization.** Currency and unit scaling (Cr, Lakh, K, M), Indian fiscal-year period parsing, and alias-based metric matching, so "ARR" and "Annual Recurring Revenue" from two documents resolve to the same metric.
- **Cross-document consistency engine.** Groups metrics by name and period across documents and flags disagreements with a severity level. Comparisons it cannot justify (for example "Year 1" versus "2025") are skipped rather than guessed.
- **Evidence-linked risk rules.** Named, inspectable rules (burn versus revenue, cash runway, unsupported-claim ratio, cross-document discrepancies). Each flag cites the data that triggered it. No LLM-generated risk scores.
- **Grounded chat.** Embedding-based retrieval over the findings, with page-level citations on every answer. If the documents don't contain the answer, it says so.
- **Analysis workspace.** Every metric and claim, grouped and filterable, with verification status and related risk flags.
- **Document comparison.** Side-by-side completeness and evidence-coverage breakdown for any two documents, with no recommendation attached.
- **Dashboard and PDF report.** Risk heatmap, contradiction matrix, metric charts, and an exportable report with a dedicated Data Gaps section.
- **Session history.** Past analyses are saved and can be reopened.

## How it works

```
Upload PDFs
    │
    ▼
1. Extraction ──────── PyMuPDF text + Tesseract OCR fallback → schema-validated LLM output
    │
    ▼
2. Canonicalization ── currency / unit / fiscal-period / metric-name normalization (no LLM)
    │
    ▼
3. Consistency ─────── cross-document metric reconciliation + unsupported-claim detection
    │
    ▼
4. Risk rules ──────── named rules, each linked to its evidence
    │
    ├──▶ 5. Chat ────── embeddings + cosine similarity, answers only from findings
    └──▶ 6. Report ──── structured PDF rendered from the same findings
```

The chat, dashboard, and report all render from the same findings data, so they can never disagree with each other.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic |
| Document processing | PyMuPDF, Tesseract OCR (pytesseract), Pillow |
| LLM and embeddings | OpenAI API (structured outputs, `text-embedding-3-small`) |
| Retrieval | NumPy cosine similarity over a JSON-backed vector store |
| Persistence | SQLite |
| Reports | ReportLab |
| Frontend | React, Vite, React Router, Recharts, Axios |

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # pdf_parser, ocr, extractor, canonicalizer, consistency_engine,
│   │   │                     # risk_rules, risk_engine, vector_store, chat_engine,
│   │   │                     # report_generator, session_store
│   │   ├── db.py
│   │   └── main.py
│   ├── eval/                 # evaluation harness and ground truth
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/            # Home, Chat, Analysis, Documents, History
        ├── components/       # Dashboard, ChatPanel, StampBadge
        ├── context/          # shared session state
        └── api.js
```

## Getting started

### Prerequisites

- Python 3.11 (newer versions may lack prebuilt wheels for PyMuPDF)
- Node.js 18+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
  - Windows: install the [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki) to the default path
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
- An OpenAI API key

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
python -m pip install -r requirements.txt
```

Create `backend/.env`:

```
OPENAI_API_KEY=your_key_here
ALLOWED_ORIGINS=http://localhost:5173
```

Run it:

```bash
python -m uvicorn app.main:app --reload --reload-dir app --port 8000
```

`--reload-dir app` keeps the dev server from restarting every time a result file is written elsewhere in the folder.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, go to **Chat**, enter a company name, and upload one or more PDFs.

For a deployed backend, set `VITE_API_URL` (including the `/api` suffix) in the frontend's environment.

## API overview

| Endpoint | Purpose |
|---|---|
| `POST /api/documents/extract` | Parse a PDF and extract structured metrics and claims |
| `POST /api/documents/canonicalize` | Normalize units, periods, and metric names |
| `POST /api/documents/consistency-check` | Cross-document discrepancies and unsupported claims |
| `POST /api/documents/risk-assessment` | Run the risk rule engine |
| `POST /api/documents/generate-report` | Generate the PDF report |
| `POST /api/chat/index` | Index findings for chat |
| `POST /api/chat/query` | Ask a grounded question |
| `POST /api/chat/opening-summary-direct` | Generate the proactive opening summary |
| `GET/POST/DELETE /api/sessions` | Save, list, load, and delete analyses |

Interactive docs are available at `http://localhost:8000/docs` while the backend is running.

## Evaluation

The `backend/eval/` folder contains a harness that runs test documents through the live pipeline and compares the output against hand-labeled ground truth: expected cross-document discrepancies, expected unsupported claims, and a minimum extraction count. One test case is a deliberately degraded scanned deck, which exercises the OCR path.

Place your test PDFs in `backend/test_documents/` (not committed), start the backend, then:

```bash
python eval/run_eval.py
```

Results are written to `backend/eval/eval_report.json`.

## Deployment

- **Frontend:** Vercel (root directory `frontend`, environment variable `VITE_API_URL`). `vercel.json` rewrites all routes to `index.html` for client-side routing.
- **Backend:** any Docker-capable host (for example Render). The `Dockerfile` installs Tesseract. Set `OPENAI_API_KEY` and `ALLOWED_ORIGINS` (your frontend URL) as environment variables.

## Known limitations

- Metrics reported with relative periods ("Year 1") are intentionally not compared against absolute years, since mapping them would require an unstated assumption.
- Metrics outside the alias dictionary are labeled "Uncategorized" rather than force-matched. Extend `metric_aliases.py` to cover more terms.
- Completeness and risk-heatmap values are transparent heuristics, not statistically validated scores.
- SQLite and the vector store live on local disk, so on hosts with ephemeral filesystems saved sessions reset on restart.
- There is no user authentication or rate limiting, so a public deployment lets anyone spend your OpenAI credits. Keep a usage cap set on your API key.
- Extraction quality depends on the LLM and can miss sections of a deck.

## Disclaimer

Evidence Ledger is a document-verification aid. It does not provide investment, legal, or financial advice.
