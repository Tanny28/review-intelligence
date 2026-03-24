<div align="center">
  <img src="https://img.shields.io/badge/Status-Live_in_Production-success?style=for-the-badge&logo=rocket" alt="Live in Production">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/API-Flask-000000?style=for-the-badge&logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/AI-HuggingFace-F9AB00?style=for-the-badge&logo=huggingface" alt="AI">
  <br>

  <h1>🔍 Enterprise Review Intelligence System</h1>
  <p><b>AI-powered customer feedback analysis for Banking, FMCG, Pharma & Fragrance industries</b></p>
  
  <a href="https://review-intelligence.streamlit.app/"><strong>🔥 View Live Dashboard Here</strong></a> | 
  <a href="https://review-intelligence.onrender.com/"><strong>⚙️ Access REST API</strong></a>

</div>

<br>

## 🚀 Live Demos
- **Frontend Dashboard:** [review-intelligence.streamlit.app](https://review-intelligence.streamlit.app/)
- **Microservice API:** [review-intelligence.onrender.com](https://review-intelligence.onrender.com) (Rate Limited)

---

## 🏗️ Architecture & Features

This system automatically aggregates reviews across the internet (Google Maps, Trustpilot, Amazon) and runs them through a sophisticated multi-model NLP pipeline to surface executive insights, competitive intelligence, and crisis warnings.

### ✨ Key Features
- **🌐 Smart Serper.dev Scraper:** Defeats anti-bot measures to dynamically scrape live data from Google Search/Maps based purely on a brand name layout.
- **🧠 Triple-Ensemble NLP Sentiment:** Combines `distilBERT` (Transformer), `VADER` (Rule-based), and `TextBlob` (Lexicon) into a geometrically averaged sentiment powerhouse. 
- **⚠️ Real-time Crisis Detection:** Actively scans for legal threats, health risks, or public-relations nightmares and flashes CRITICAL alerts on the dashboard.
- **📄 Downloadable PDF Reports:** Compiles live visual charts and statistical matrices directly into a dynamic `io.BytesIO` PDF report for C-suite distribution.
- **🤖 Groq Llama3 Agent:** Generates an executive summary and competitive positioning analysis directly from the text patterns within seconds.

---

## 🛠️ Tech Stack & Deployment

We utilize a robust split-brain environment configured for extreme reliability on $0 PaaS tiers:

| Component | Technology | Cloud Host |
| :--- | :--- | :--- |
| **Frontend Platform** | Streamlit, Plotly, Pandas | Streamlit Community Cloud |
| **Backend API Server** | Flask, Gunicorn, Flask-Limiter | Render.com |
| **Scraping Engine** | Serper API, BeautifulSoup4, Fake-UserAgent | *Native* |
| **Machine Learning** | PyTorch (CPU), HuggingFace Transformers, Spacy | *Native* |
| **Generative AI** | Groq (Llama-3-8b-8192) | Cloud API |

---

## 💻 API Developer Usage
This system exposes a highly constrained, rate-limited public API built on Flask. You can submit POST requests from anywhere in the world to analyze customer sentiment dynamically.

```bash
curl -X POST https://review-intelligence.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d "{\"industry\": \"FMCG\", \"use_sample\": true}"
```

*(Note: API access uses `flask-limiter` configured for 5 requests per minute against IP routing abuse.)*

---

> Built with ❤️. Hosted entirely free for portfolio demonstration.