# ⚜️ Zomato Royal Concierge — AI Restaurant Recommendation Engine

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq LPU](https://img.shields.io/badge/Groq-LPU%20Inference-F05A28?logo=groq&logoColor=white)](https://groq.com/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?logo=vercel&logoColor=white)](https://vercel.com/)
[![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E?logo=railway&logoColor=white)](https://railway.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, **Hybrid Retrieval-Augmented Recommendation (HRAR)** system combining deterministic tabular filtering (Polars & DuckDB) with sub-second semantic LLM re-ranking (Groq LPU Cloud). Designed to deliver personalized dining discoveries with zero hallucinations and instant heuristic fallback.

---

## 🌟 Key Features

- **Decoupled Architecture**: High-performance dark luxury web SPA hosted on **Vercel** communicating with containerized FastAPI backend on **Railway**.
- **Blazing Fast Inference**: Sub-second recommendation reasoning powered by Groq LPUs (`qwen/qwen3.8-27b` / `llama-3.3-70b-versatile`).
- **Deterministic Pre-Filtering**: Over 51,000+ restaurant records pruned down to top candidates in $< 35\text{ms}$ using columnar Apache Parquet and Polars/DuckDB.
- **Zero-Hallucination Grounding**: Post-generation validator verifies every recommended eatery, rating, and price against ground-truth data.
- **Fail-Safe Self-Healing Fallback**: Automatic instant fallback to multi-factor Bayesian heuristic ranking if the external LLM encounters rate limits or network degradation.
- **Modern Luxury UI**: Dark Nocturne Haute Gastronomie design matching Google Stitch standards with real-time latency diagnostics.

---

## 🏗️ System Architecture

```
  ┌──────────────────────────────────────────────────────────────┐
  │                 Vercel Global Edge Network                   │
  │     (Static Luxury SPA Frontend & Edge Reverse Proxy)        │
  └──────────────────────────────┬───────────────────────────────┘
                                 │  /api/* (Edge Proxy Rewrite)
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                   Railway Container Service                  │
  │     (Uvicorn ASGI Server + FastAPI REST Application)         │
  ├──────────────────────────────┬───────────────────────────────┤
  │                              │                               │
  │     Columnar Retrieval       │      Groq LPU Inference       │
  │   (Polars, DuckDB & Parquet) │     (qwen/qwen3.8-27b)        │
  └──────────────────────────────┴───────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Clone Repository & Setup Environment

```bash
git clone https://github.com/fxdarshan/Zomato-Restaurant-Recommendation.git
cd Zomato-Restaurant-Recommendation

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment template and add your Groq API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=qwen/qwen3.8-27b
PORT=8000
HOST=0.0.0.0
```

### 3. Run Locally

#### Option A: Run with Batch Script (Windows)
```bash
run_app.bat
```

#### Option B: Run via Docker Compose
```bash
docker compose up --build
```

#### Option C: Run FastAPI Directly
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Web Application**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📦 Production Deployment

Complete step-by-step instructions for deploying to **Vercel** (Frontend) and **Railway** (Backend) are available in:
👉 **[Doc/deployment-plan.md](Doc/deployment-plan.md)**

### Deployment Overview:
1. **Backend on Railway**: Import repository into Railway $\rightarrow$ Add `GROQ_API_KEY` $\rightarrow$ Generate domain.
2. **Frontend on Vercel**: Import repository into Vercel (Root Directory: `frontend`) $\rightarrow$ Update Railway URL in `frontend/vercel.json` $\rightarrow$ Deploy.

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
pytest -v
```

All 49 unit and integration tests covering data pipelines, retrieval filters, LLM grounding, and configuration pass with 100% compliance.

---

## 📚 Documentation

- [Deployment Plan (Vercel + Railway)](Doc/deployment-plan.md)
- [System Architecture](Doc/architecture.md)
- [Implementation Roadmap](Doc/implementation-plan.md)
- [Edge Case Handling](Doc/edge-case.md)
- [Evaluation Metrics & Benchmarks](Doc/eval.md)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
