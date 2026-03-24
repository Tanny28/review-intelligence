# 🔍 Review Intelligence System

> **NLP feedback intelligence demo for Banking, FMCG, Pharma & Fragrance.**  
> Turn **sample or scraped** review text into sentiment, aspects, crisis signals, Groq-powered summaries, and PDF export.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit)
![Flask](https://img.shields.io/badge/Flask-REST_API-black?style=flat-square&logo=flask)
![NLP](https://img.shields.io/badge/NLP-VADER_|_TextBlob_|_spaCy-green?style=flat-square)
![AI](https://img.shields.io/badge/AI-Groq_Llama_3.1-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## ✅ Implementation status (truth table)

This repo is a **solid demo**: Streamlit UI, two-model sentiment, keyword aspects, spaCy NER, Groq summaries, ReportLab PDF, and Flask endpoints. It is **not** hardened for production abuse or for guaranteed extraction from **Google Maps / Amazon / Trustpilot** without extra (often **paid**) tooling.

| Capability | Shipped? | What the code actually does |
|------------|----------|-----------------------------|
| Demo / sample reviews per industry | Yes | `SAMPLE_DATA` in `scraper.py`; primary happy path. |
| “Any URL” live reviews | Partial | `requests` + BeautifulSoup only; many sites block bots, need JS, or return useless HTML. |
| Dedicated Maps / Amazon / Trustpilot scrapers | No | No site-specific parsers; Selenium is in `requirements.txt` but **not wired** in `scraper.py`. |
| Sentiment | Yes | **VADER + TextBlob** averaged → `final_score` and Positive/Negative/Neutral. **No HuggingFace/distilBERT** in the analysis loop. |
| Aspect labels | Yes | **Industry keyword dictionaries** (`classify_aspect`), not NER-based tagging. |
| spaCy | Yes | **Named-entity extraction** per review (`entities` column). |
| TF-IDF | Yes | **Corpus top terms** via `get_top_keywords()` — not the main aspect classifier. |
| Crisis alerts | Yes | See [Crisis detection](#crisis-detection) for the full rule set. |
| Groq executive summary | Yes | `llama-3.1-8b-instant`; swap if Groq [deprecates](https://console.groq.com/docs/deprecations) the ID. |
| PDF export | Yes | `report.py` + dashboard download (PDF bytes cached in session after generation). |
| Flask API | Yes | **No** rate limiting or input hardening in-tree — add before a public launch. |

### Architecture (data flow)

```
URL + industry  ──▶  scraper.py  ──▶  DataFrame (review_text, rating, date, …)
                         │
                         ▼
              nlp_engine.run_full_analysis
                • VADER + TextBlob → final_score / final_label
                • Keyword map → aspect
                • spaCy → entities
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   check_crisis    get_summary_stats    (optional) Groq → AI bullets
         │               │               │
         └───────────────┴───────────────┘
                         │
              Streamlit dashboard  │  Flask JSON  │  report.py PDF
```

### “Completely free” production note

- **Groq** = usable **free tier**, not unlimited; protect `GROQ_API_KEY` (env only, rate limits on the API).
- **Dependable** scraping of major review UIs usually means **paid** APIs (SerpAPI, Apify, …) or brittle DIY browsers with **ToS** risk.
- A honest **$0** product story: **sample data**, **small curated URLs**, or future **CSV upload** — plus `gunicorn`, `flask-limiter`, validation, and logging when you expose Flask.

---

## 📸 Dashboard Preview

> **Live Demo:** [review-intelligence.streamlit.app](https://review-intelligence.streamlit.app) *(add your link here)*

---

## 🚀 What It Does

The pipeline in 6 steps:

```
Scrape → Analyze → Classify → Alert → Summarize → Display
```

| Stage | What happens |
|-------|-------------|
| **Scrape** | Sample datasets by industry; optional generic HTML fetch (best-effort, not Maps/Amazon/Trustpilot-specific) |
| **Analyze** | **VADER + TextBlob** combined for polarity; spaCy for entities |
| **Classify** | Keyword-based aspects per industry (pricing, delivery, quality, etc.) |
| **Alert** | Rule-based crisis flags on negative %, rating, and mean sentiment score |
| **Summarize** | Llama 3.1-class model on **Groq** → complaints / strengths / action |
| **Display** | Streamlit + Plotly + optional Flask JSON + PDF download |

---

## 🏭 Industries Supported

| Industry | Tracked Aspects |
|----------|----------------|
| 🏦 **Banking** | Fees, interest rates, digital experience, customer service, loan processing |
| 🛒 **FMCG** | Product quality, delivery, packaging, freshness, pricing |
| 💊 **Pharma** | Efficacy, side effects, dosage, pricing, availability |
| 🌸 **Fragrance** | Longevity, scent profile, packaging, value for money |

---

## 🧠 Tech Stack

### NLP Pipeline
- **VADER** — compound polarity → score + label
- **TextBlob** — polarity + subjectivity (combined with VADER for `final_score`)
- **spaCy** — named entity recognition (`en_core_web_sm`)
- **Keyword maps** — per-industry aspect tags (not NER-driven)
- **TF-IDF** (optional helper) — top keywords across the corpus in `get_top_keywords()`
- *`transformers` / `torch` appear in `requirements.txt` but are **not** used by the main sentiment path today.*

### Backend & API
- **Flask** — REST API with `/analyze` and `/summary` endpoints
- **Groq (LLaMA 3.1)** — AI-generated executive summaries

### Frontend
- **Streamlit** — interactive dashboard with real-time analysis
- **Plotly** — sentiment trend charts, aspect bar charts, pie charts

### Export
- **ReportLab** — professional multi-page PDF reports

---

## ⚡ Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/review-intelligence.git
cd review-intelligence
```

### 2. Set up environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('stopwords'); nltk.download('punkt')"
```

### 3. Add your API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key at [console.groq.com](https://console.groq.com)

### 4. Run the dashboard
```bash
streamlit run dashboard.py
```

### 5. Run the API (optional)
```bash
python api.py
```

---

## 🔌 REST API

### Endpoints

#### `GET /`
Health check — returns API version and available endpoints.

#### `POST /analyze`
Full NLP analysis pipeline.

**Request:** `industry`, optional `url`, and `use_sample` (default `true`). If `use_sample` is `false`, you **must** supply a `url` the scraper can parse.

```json
{
  "industry": "FMCG",
  "use_sample": true
}
```

**Response:**
```json
{
  "status": "success",
  "industry": "FMCG",
  "total_reviews": 50,
  "summary": {
    "positive_pct": 62.0,
    "negative_pct": 24.0,
    "avg_rating": 3.8,
    "top_aspect": "Product Quality"
  },
  "crisis_alerts": [],
  "aspect_breakdown": { "Product Quality": 18, "Delivery": 12 },
  "top_negative_reviews": [...]
}
```

#### `POST /summary`
AI-generated executive summary using LLaMA 3.1.

**Request:**
```json
{
  "industry": "Banking",
  "use_sample": true
}
```

**Response:**
```json
{
  "status": "success",
  "ai_summary": {
    "complaints": ["High transaction fees frustrate long-term customers", "..."],
    "strengths": ["Mobile app praised for speed and UX", "..."],
    "recommended_action": "Introduce fee waiver program for customers with 2+ year tenure"
  }
}
```

---

## 📁 Project Structure

```
review-intelligence/
│
├── scraper.py          # Web scraping + sample data generation
├── nlp_engine.py       # VADER + TextBlob sentiment, keywords, spaCy NER, crisis helpers
├── dashboard.py        # Streamlit frontend
├── api.py              # Flask REST API
├── report.py           # PDF export (ReportLab)
│
├── requirements.txt    # All dependencies
├── .env                # API keys (never commit this)
├── .gitignore
└── README.md
```

---

## 🚨 Crisis detection

Rules in `check_crisis()` (alerts can stack):

| Level | Trigger |
|-------|---------|
| **CRITICAL** | Negative reviews ≥ **40%** of all rows |
| **WARNING** | Negative reviews ≥ **25%** (and &lt; 40%) |
| **CRITICAL** | Average rating &lt; **3.0** / 5 |
| **WARNING** | Average rating &lt; **3.5** / 5 (and not already worse) |
| **CRITICAL** | Mean `final_score` &lt; **-0.1** |

Alerts surface in the Streamlit dashboard, API JSON, and PDF export. *There is no separate “rolling 7-day window” in code unless your `date` column reflects that.*

---

## 📄 PDF Report

Click **"Download PDF Report"** in the dashboard to export a professional report containing:
- Executive overview metrics
- Crisis alerts (if triggered)
- Sentiment distribution table
- Aspect/topic breakdown
- AI-generated complaints, strengths & recommended action
- Sample reviews (positive, negative, neutral)

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) — LLM inference (free tier for development)
- [Streamlit](https://streamlit.io) & [Plotly](https://plotly.com/python/)
- [spaCy](https://spacy.io), [NLTK](https://www.nltk.org/), [TextBlob](https://textblob.readthedocs.io/)
- [ReportLab](https://www.reportlab.com/)