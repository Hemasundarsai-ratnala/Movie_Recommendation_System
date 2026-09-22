# Backend — Hybrid Movie Recommendation Engine

FastAPI-powered machine learning backend combining:
- **TF-IDF Content Filtering**
- **Centered Cosine Item-Based Collaborative Filtering**
- **RapidFuzz Title Aliasing & Fuzzy Matching**
- **Bayesian Weighted Popularity Ranking & MMR Diversity Re-ranking**

---

## 📁 Directory Structure

```
backend/
├── app/
│   ├── api/             # API route endpoints (/health, /movies, /recommend, /insights)
│   ├── models/          # Trained model artifacts (.joblib, training_manifest.json)
│   ├── services/        # Recommender engine, similarity computation, ranking
│   ├── config.py        # Central environment configuration & safe defaults
│   ├── logging_config.py# Structured logging configuration
│   ├── main.py          # FastAPI application entry point & CORS
│   └── schemas.py       # Pydantic request/response schemas
├── scripts/
│   ├── train.py         # Offline model training & serialization pipeline
│   ├── evaluate.py      # Offline evaluation metrics (Precision@K, NDCG@K, Recall@K)
│   └── validate_data.py # Dataset integrity checks
├── Dockerfile           # Backend containerization
├── requirements.txt     # Python dependencies
└── README.md
```

---

## 🚀 Quickstart (Standalone)

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Train Models
```bash
python backend/scripts/train.py
```

### 3. Run FastAPI Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

---

## 🔗 Linking with Frontend

- **CORS Configuration**: The backend automatically permits requests from `http://localhost:5173`, `http://localhost:3000`, and `*.vercel.app` (configured in `backend/app/config.py`).
- **Proxying**: The React frontend proxies `/api/*` requests to port `8000` automatically during local development.
