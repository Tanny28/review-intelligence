from flask import Flask, request, jsonify
from scraper import scrape_reviews
from nlp_engine import run_full_analysis, check_crisis, get_summary_stats
from groq import Groq
from dotenv import load_dotenv
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)

# Set up rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["100/day", "10/minute"])

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VALID_INDUSTRIES = ["FMCG", "Banking", "Pharma", "Fragrance"]


# ── Health check ────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Review Intelligence API",
        "version": "1.0.0",
        "endpoints": ["/analyze", "/summary", "/health"]
    })


# ── Main analysis endpoint ───────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
@limiter.limit("5/minute")
def analyze():
    """
    POST /analyze
    Body: { "url": "https://...", "industry": "FMCG", "use_sample": true }
    Returns: sentiment scores, aspect breakdown, crisis alerts
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    industry = data.get("industry", "FMCG")
    url = data.get("url", "")
    use_sample = data.get("use_sample", True)

    if industry not in VALID_INDUSTRIES:
        return jsonify({
            "error": f"Invalid industry. Choose from: {VALID_INDUSTRIES}"
        }), 400

    if not use_sample and not url:
        return jsonify({
            "error": "Provide a 'url' or set 'use_sample' to true"
        }), 400

    try:
        # Run the full pipeline
        df_raw = scrape_reviews(url=url, industry=industry, use_sample=use_sample)
        df = run_full_analysis(df_raw, industry)
        stats = get_summary_stats(df)
        alerts = check_crisis(df)

        # Build aspect breakdown dict
        aspect_counts = df['aspect'].value_counts().to_dict()

        # Sentiment distribution
        sentiment_counts = df['final_label'].value_counts().to_dict()

        # Top 5 reviews per sentiment
        top_negative = (
            df[df['final_label'] == 'Negative'][['review_text', 'final_score', 'aspect', 'rating']]
            .head(5)
            .to_dict(orient='records')
        )
        top_positive = (
            df[df['final_label'] == 'Positive'][['review_text', 'final_score', 'aspect', 'rating']]
            .head(5)
            .to_dict(orient='records')
        )

        return jsonify({
            "status": "success",
            "industry": industry,
            "total_reviews": stats['total_reviews'],
            "summary": {
                "positive_pct": stats['positive_pct'],
                "negative_pct": stats['negative_pct'],
                "neutral_pct": round(100 - stats['positive_pct'] - stats['negative_pct'], 1),
                "avg_rating": stats['avg_rating'],
                "top_aspect": stats['top_aspect']
            },
            "sentiment_distribution": sentiment_counts,
            "aspect_breakdown": aspect_counts,
            "crisis_alerts": alerts,
            "top_negative_reviews": top_negative,
            "top_positive_reviews": top_positive
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── AI summary endpoint ──────────────────────────────────────────────────────
@app.route("/summary", methods=["POST"])
@limiter.limit("5/minute")
def ai_summary():
    """
    POST /summary
    Body: { "url": "https://...", "industry": "FMCG", "use_sample": true }
    Returns: AI-generated executive summary of complaints, strengths, action
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    industry = data.get("industry", "FMCG")
    url = data.get("url", "")
    use_sample = data.get("use_sample", True)

    if industry not in VALID_INDUSTRIES:
        return jsonify({
            "error": f"Invalid industry. Choose from: {VALID_INDUSTRIES}"
        }), 400

    if not os.getenv("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY not configured on server"}), 503

    try:
        df_raw = scrape_reviews(url=url, industry=industry, use_sample=use_sample)
        df = run_full_analysis(df_raw, industry)

        neg_reviews = df[df['final_label'] == 'Negative']['review_text'].head(10).tolist()
        pos_reviews = df[df['final_label'] == 'Positive']['review_text'].head(5).tolist()

        prompt = f"""
You are a business analyst for a {industry} company.
Analyze these customer reviews and provide:
1. Top 3 complaints (one line each, under 15 words)
2. Top 2 strengths (one line each, under 15 words)
3. One urgent action recommendation (under 20 words)

Negative reviews: {neg_reviews}
Positive reviews: {pos_reviews}

Format your response exactly like:
COMPLAINTS:
- complaint 1
- complaint 2
- complaint 3

STRENGTHS:
- strength 1
- strength 2

ACTION: your recommendation
"""
        chat = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        summary_text = chat.choices[0].message.content

        # Parse into structured JSON
        complaints, strengths, action = [], [], ""
        in_complaints = in_strengths = False

        for line in summary_text.strip().split('\n'):
            if 'COMPLAINTS' in line:
                in_complaints, in_strengths = True, False
            elif 'STRENGTHS' in line:
                in_complaints, in_strengths = False, True
            elif 'ACTION:' in line:
                in_complaints = in_strengths = False
                action = line.replace('ACTION:', '').strip()
            elif in_complaints and line.startswith('- '):
                complaints.append(line[2:].strip())
            elif in_strengths and line.startswith('- '):
                strengths.append(line[2:].strip())

        return jsonify({
            "status": "success",
            "industry": industry,
            "ai_summary": {
                "complaints": complaints,
                "strengths": strengths,
                "recommended_action": action,
                "raw": summary_text
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, port=5000)
