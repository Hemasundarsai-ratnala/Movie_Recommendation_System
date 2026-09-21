# Hybrid Movie Recommendation System

A production-grade, end-to-end **Hybrid Movie Recommendation System** combining Content-Based Filtering (TF-IDF), Item-Based Collaborative Filtering (Centered Cosine + Shrinkage), RapidFuzz Title Search Aliasing, and Bayesian Weighted Popularity Ranking.

---

## Architecture Diagram

```mermaid
flowchart TD
    User([User Input Query / Seed Ratings]) --> NLP[NLP Title Normalization & Alias Search Index]
    NLP --> Matcher{RapidFuzz Confidence Thresholds}
    Matcher -->|>= 85: Auto-Accept| Resolved[Resolved Seed MovieId]
    Matcher -->|60-84: Did You Mean| Suggest[Did You Mean Suggestions]
    Matcher -->|< 60: No Match| ColdStart[Cold Start Bayesian Popularity]

    Resolved --> PrefWeight[Preference Weight Transformation: w = rating - 3.0]
    
    PrefWeight --> Content[Content Model: TF-IDF + Top-200 Sparse Cosine]
    PrefWeight --> Collab[Collaborative Model: Centered Cosine + Shrinkage n/(n+25)]
    
    Content --> Agg[Multi-Movie Score Accumulation by MovieId]
    Collab --> Agg
    
    Agg --> Exclude[Exclude Seed Movies from Candidates]
    Exclude --> ChannelNorm[Channel Min-Max Score Normalization]
    ChannelNorm --> WeightRenorm[Missing-Channel Weight Renormalization]
    WeightRenorm --> Fusion[Hybrid Fusion: 0.45 Content + 0.45 Collab + 0.10 Popularity]
    Fusion --> MMR[MMR Diversity Re-Ranking λ=0.7]
    MMR --> Explanation[Signal Contribution Explanation Builder]
    Explanation --> API[FastAPI JSON Response]
    API --> UI[React Cinematic Web UI]
```

---

## Verified Dataset Facts (MovieLens 100k)

| Property | Value |
|---|---|
| `movies.csv` | 9,742 rows × 3 cols (`movieId`, `title`, `genres`) |
| `ratings.csv` | 100,836 rows × 4 cols (`userId`, `movieId`, `rating`, `timestamp`) |
| Null values | **0**, across all columns |
| Duplicate `movieId` / `(userId, movieId)` | **0** |
| Unique Users | 610 |
| Unique Rated Movies | 9,724 |
| Global Mean Rating | **3.5016** |
| Matrix Sparsity | **98.3%** |
| Duplicate Title Pairs | 5 pairs (`Emma`, `Saturn 3`, `Eros`, `War of the Worlds`, `Confessions of a Dangerous Mind`) |
| Zero-Rating Movies | 18 movies |
| Zero-Genre Movies | 34 movies (`(no genres listed)`) |
| Titles lacking year `(YYYY)` | 13 movies (`Babylon 5`, `Ready Player One`, etc.) |

---

## Machine Learning & NLP Methodology

### 1. Title Aliasing & RapidFuzz Search Index
To resolve inverted titles like `"Dark Knight, The (2008)"` or secondary titles like `"Seven (a.k.a. Se7en) (1995)"`, titles are preprocessed at training time into searchable aliases:
- Unfolding trailing articles: `Matrix, The` $\rightarrow$ `the matrix` and `matrix`
- Secondary paren group splitting: `Seven (a.k.a. Se7en)` $\rightarrow$ `se7en` and `seven`
- Diacritics NFKD normalization to ASCII: `Misérables, Les` $\rightarrow$ `les miserables`
- De-spaced and de-apostrophized variants: `darkknight`, `schindlers list`

Confidence thresholding:
- $\ge 85$: Auto-accept match
- $60 - 84$: "Did you mean..." suggestions
- $< 60$: No confident match found

### 2. Content-Based Model
TF-IDF vectorizer fitted over `normalized_title_tokens + genre_tokens + decade_bucket`. Block-wise top-200 sparse cosine similarity calculation to prevent dense $9,742^2$ matrix allocation.

### 3. Item-Based Collaborative Model
- User ratings are mean-centered over observed entries only: $\tilde{r}_{u,i} = r_{u,i} - \bar{r}_u$.
- Centered cosine similarity (Pearson on co-rated items) computed on sparse CSR.
- Shrinkage confidence weighting applied: $sim_{adjusted} = sim_{raw} \times \frac{n}{n + 25}$.
- $MIN\_COMMON\_RATINGS = 20$ floor (1,297 eligible movies).

### 4. Bayesian Weighted Rating ($WR$)
$$WR = \frac{v}{v + m} R + \frac{m}{v + m} C$$
$m = 50$, $C = 3.5130$ (computed exclusively on training split during evaluation).
For candidate ranking, a support-scaled popularity score is used:
$$\text{PopularityScore} = WR \times \frac{\ln(1 + v)}{\ln(1 + V_{\max})}$$
This preserves the honest Bayesian $WR$ for user-facing display while ensuring that low-support movies ($v \le 3$) cannot artificially outrank well-supported catalog favorites in candidate score normalization.

### 5. Preference Weight & Score Fusion
$$w_s = \text{rating}_s - 3.0$$
Disliked movies ($r < 3.0$) yield negative weights, suppressing candidate neighbours. Scores accumulate into a dictionary by `movieId` (never appending series).

Score channels are min-max normalized across the candidate pool. Unmodified configured weights ($W_{\text{content}}=0.45, W_{\text{collab}}=0.45, W_{\text{pop}}=0.10$) are applied directly ($H = W_c \cdot c_n + W_{cb} \cdot cb_n + W_p \cdot p_n$), ensuring missing collaborative evidence naturally down-weights candidates rather than artificially inflating content weights.

---

## Offline Evaluation Results (80/20 Temporal Split, 610 Users)

Evaluated on held-out rating threshold $\ge 4.0$ with zero data leakage (all train interactions excluded from recommendations; recency-prioritized seed selection):

| Model | P@5 | P@10 | R@5 | R@10 | NDCG@5 | NDCG@10 | HitRate@10 | Catalog Coverage |
|---|---|---|---|---|---|---|---|---|
| **B1 Most-Popular (Non-personalized)** | 0.0680 | 0.0530 | 0.0289 | 0.0499 | 0.0798 | 0.0738 | 31.47% | 0.31% |
| **B2 Content-only** | 0.0149 | 0.0127 | 0.0073 | 0.0108 | 0.0172 | 0.0167 | 10.32% | 16.82% |
| **B3 Collaborative-only** | 0.0829 | 0.0655 | 0.0429 | 0.0676 | 0.0949 | 0.0907 | 38.41% | 5.99% |
| **B4 Hybrid (production, $\lambda=0.70$)** | 0.0741 | 0.0623 | 0.0398 | 0.0653 | 0.0859 | 0.0862 | 40.10% | 10.73% |
| **B4 Hybrid (diagnostic relevance, $\lambda=1.0$)** | 0.0728 | 0.0562 | 0.0412 | 0.0584 | 0.0850 | 0.0802 | 36.04% | 9.32% |

---

## Project Structure

```
movie-recommendation-system/
├── run.py                       Unified pipeline: validate -> train -> eval -> serve
├── data/                        movies.csv, ratings.csv
├── notebooks/                   movie_recommendation_analysis.ipynb
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, schemas.py, logging_config.py
│   │   ├── api/                 health.py, movies.py, recommendations.py, insights.py
│   │   ├── services/            recommender.py, content_model.py, collaborative_model.py,
│   │   │                        fuzzy_matcher.py, hybrid_model.py, ranking.py, explain.py
│   │   └── utils/               preprocessing.py, validation.py
│   ├── scripts/                 train.py, evaluate.py, validate_data.py
│   └── requirements.txt, Dockerfile
├── frontend/                    React + Vite app
├── tests/                       Pytest test suite (17 passed)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Installation & Commands

### Setup Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
```

---

### Quick Start — Single Command (Recommended)

`run.py` chains **validate → train → evaluate → serve** in one shot:

```bash
# Full pipeline: validate data, train models, run evaluation, then start server
python run.py

# Skip training if artifacts already exist (fast re-start)
python run.py --skip-train

# Skip training AND evaluation (just start the server)
python run.py --skip-train --skip-eval

# Custom host / port
python run.py --skip-train --skip-eval --host 0.0.0.0 --port 8080
```

| Flag | Default | Description |
|---|---|---|
| `--skip-train` | `False` | Skip data validation + model training (reuse saved artifacts) |
| `--skip-eval` | `False` | Skip offline evaluation / benchmark run |
| `--host` | `127.0.0.1` | Server host address |
| `--port` | `8000` | Server port |

---

### Individual Commands (for reference)

#### 1. Data Validation
```bash
python backend/scripts/validate_data.py
```

#### 2. Offline Model Training
```bash
python backend/scripts/train.py
```

#### 3. Run Offline Evaluation
```bash
python backend/scripts/evaluate.py
```

#### 4. Run Pytest Suite
```bash
# Windows (PowerShell):
$env:PYTHONPATH="."
.venv\Scripts\python.exe -m pytest tests/

# Linux/macOS:
PYTHONPATH=. pytest tests/
```

#### 5. Run Backend Server (standalone)
```bash
uvicorn backend.app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/docs`

#### 6. Run Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
```
UI available at: `http://localhost:5174`

### 7. Run with Docker Compose
```bash
docker-compose up --build
```

### 8. Deploy to Vercel
The project is fully configured for deployment on Vercel out of the box with `vercel.json`, `api/index.py` (FastAPI serverless function), and pre-trained model artifacts:

#### Option A: Deploy via GitHub (Recommended)
1. Push this repository to GitHub.
2. Go to [Vercel Dashboard](https://vercel.com/new) and click **"Add New Project"**.
3. Import the GitHub repository.
4. Leave all build and output settings as default — Vercel will automatically read `vercel.json`.
5. Click **"Deploy"**.

#### Option B: Deploy via Vercel CLI
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

The deployment serves:
- **React Frontend**: Built from `frontend/` to `frontend/dist` with client-side SPA routing.
- **FastAPI Backend**: Serverless execution at `/api/...`, `/docs`, and `/openapi.json` via `api/index.py`.
- **Model Artifacts**: Pre-trained model artifacts are packaged directly within the serverless function.

---

## Known Limitations

1. **Dataset Size**: MovieLens 100k contains 610 users and 9,742 movies (98.3% sparse).
2. **Collaborative Coverage**: Only 13.3% of movies have $\ge 20$ ratings required for robust collaborative signal.
3. **Content Features**: Features are derived from title tokens, 20 genre tags, and release decade (no cast, director, or plot keywords).
4. **Offline Evaluation Scope**: Evaluated via 80/20 temporal split without live user A/B testing.
