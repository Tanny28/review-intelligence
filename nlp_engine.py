import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import numpy as np
from datetime import datetime, timedelta

nltk.download('vader_lexicon', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

nlp = spacy.load("en_core_web_sm")

_bert_pipeline = None

def get_bert_pipeline():
    global _bert_pipeline
    if _bert_pipeline is None:
        try:
            from transformers import pipeline
            _bert_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
        except Exception as e:
            print(f"Failed to load BERT pipeline: {e}")
            _bert_pipeline = "FAILED"
    return _bert_pipeline

def analyze_sentiment_bert(text):
    pipe = get_bert_pipeline()
    if isinstance(pipe, str) and pipe == "FAILED":
        return 0.0
    try:
        result = pipe(text[:512])[0]
        score = result['score']
        return score if result['label'] == 'POSITIVE' else -score
    except Exception:
        return 0.0

ASPECT_KEYWORDS = {
    "Banking": {
        "Fees & Charges":     ["fees", "charges", "hidden", "cost", "expensive", "price", "rate", "interest"],
        "Customer Service":   ["staff", "service", "support", "helpline", "response", "helpful", "rude", "wait"],
        "Digital Experience": ["app", "online", "portal", "website", "net banking", "crash", "slow", "interface"],
        "Branch Experience":  ["branch", "ATM", "queue", "wait", "counter", "visit", "location"],
        "Products":           ["loan", "credit", "deposit", "savings", "account", "card", "investment"]
    },
    "FMCG": {
        "Product Quality":    ["quality", "taste", "smell", "texture", "genuine", "original", "fake", "bad"],
        "Packaging":          ["packaging", "pack", "box", "seal", "damaged", "leak", "plastic", "wrapper"],
        "Delivery":           ["delivery", "shipping", "late", "delay", "fast", "courier", "arrived", "dispatch"],
        "Pricing":            ["price", "expensive", "cheap", "value", "worth", "cost", "discount", "offer"],
        "Freshness":          ["fresh", "expiry", "expired", "stale", "old", "date", "shelf life"]
    },
    "Pharma": {
        "Efficacy":           ["worked", "effective", "efficacy", "relief", "symptoms", "cured", "helped", "result"],
        "Side Effects":       ["side effects", "reaction", "allergy", "nausea", "headache", "adverse", "problem"],
        "Packaging":          ["packaging", "seal", "broken", "damaged", "label", "instructions", "dosage"],
        "Pricing":            ["price", "expensive", "affordable", "cost", "cheap", "generic", "branded"],
        "Delivery":           ["delivery", "shipping", "genuine", "authentic", "fake", "expired", "cold chain"]
    },
    "Fragrance": {
        "Longevity":          ["longevity", "lasts", "hours", "long lasting", "fades", "projection", "stay"],
        "Scent Profile":      ["smell", "scent", "notes", "fragrance", "aroma", "fresh", "heavy", "sweet"],
        "Sillage":            ["sillage", "projection", "trail", "waft", "noticeable", "compliments", "strong"],
        "Packaging":          ["bottle", "packaging", "box", "design", "cap", "spray", "atomizer", "gift"],
        "Value":              ["price", "expensive", "worth", "value", "money", "budget", "luxury", "cheap"]
    }
}

def analyze_sentiment_vader(text):
    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return compound, label

def analyze_sentiment_textblob(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    return round(polarity, 3), round(subjectivity, 3)

def classify_aspect(text, industry):
    text_lower = text.lower()
    aspects = ASPECT_KEYWORDS.get(industry, ASPECT_KEYWORDS["FMCG"])
    scores = {}
    for aspect, keywords in aspects.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[aspect] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"

def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

def get_sentiment_emoji(label):
    return {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}.get(label, "😐")

def get_sentiment_color(label):
    return {"Positive": "#1D9E75", "Negative": "#E24B4A", "Neutral": "#BA7517"}.get(label, "#888780")

def run_full_analysis(df, industry):
    results = []
    for _, row in df.iterrows():
        text = row['review_text']

        vader_score, vader_label = analyze_sentiment_vader(text)
        tb_polarity, tb_subjectivity = analyze_sentiment_textblob(text)
        bert_score = analyze_sentiment_bert(text)

        # Ensemble average: VADER + TextBlob + BERT (if loaded)
        divisor = 3 if get_bert_pipeline() != "FAILED" else 2
        final_score = round((vader_score + tb_polarity + bert_score) / divisor, 3)
        
        if final_score >= 0.05:
            final_label = "Positive"
        elif final_score <= -0.05:
            final_label = "Negative"
        else:
            final_label = "Neutral"

        aspect = classify_aspect(text, industry)
        entities = extract_entities(text)

        results.append({
            "review_text":      text,
            "rating":           row.get('rating', 0),
            "date":             row.get('date', datetime.now()),
            "reviewer":         row.get('reviewer', 'Anonymous'),
            "vader_score":      vader_score,
            "vader_label":      vader_label,
            "tb_polarity":      tb_polarity,
            "tb_subjectivity":  tb_subjectivity,
            "bert_score":       bert_score,
            "final_score":      final_score,
            "final_label":      final_label,
            "aspect":           aspect,
            "entities":         str(entities),
            "emoji":            get_sentiment_emoji(final_label),
            "color":            get_sentiment_color(final_label)
        })

    return pd.DataFrame(results)

def check_crisis(df):
    alerts = []
    total = len(df)
    if total == 0:
        return alerts

    neg_pct = round(len(df[df['final_label'] == 'Negative']) / total * 100, 1)
    avg_rating = round(df['rating'].mean(), 2)
    avg_score = round(df['final_score'].mean(), 3)

    if neg_pct >= 40:
        alerts.append({
            "type": "CRITICAL",
            "message": f"Negative reviews at {neg_pct}% — immediate attention required.",
            "icon": "🚨"
        })
    elif neg_pct >= 25:
        alerts.append({
            "type": "WARNING",
            "message": f"Negative sentiment rising — {neg_pct}% of reviews are negative.",
            "icon": "⚠️"
        })

    if avg_rating < 3.0:
        alerts.append({
            "type": "CRITICAL",
            "message": f"Average rating dropped to {avg_rating}/5 — critical threshold breached.",
            "icon": "🚨"
        })
    elif avg_rating < 3.5:
        alerts.append({
            "type": "WARNING",
            "message": f"Average rating is {avg_rating}/5 — below healthy threshold of 3.5.",
            "icon": "⚠️"
        })

    if avg_score < -0.1:
        alerts.append({
            "type": "CRITICAL",
            "message": f"Overall sentiment score is {avg_score} — strongly negative signal.",
            "icon": "🚨"
        })

    return alerts

def get_top_keywords(df, n=15):
    if df.empty:
        return []
    texts = df['review_text'].tolist()
    try:
        vectorizer = TfidfVectorizer(max_features=n, stop_words='english', ngram_range=(1, 2))
        vectorizer.fit_transform(texts)
        return vectorizer.get_feature_names_out().tolist()
    except:
        return []

def get_summary_stats(df):
    if df.empty:
        return {}
    return {
        "total_reviews":    len(df),
        "positive_pct":     round(len(df[df['final_label'] == 'Positive']) / len(df) * 100, 1),
        "negative_pct":     round(len(df[df['final_label'] == 'Negative']) / len(df) * 100, 1),
        "neutral_pct":      round(len(df[df['final_label'] == 'Neutral']) / len(df) * 100, 1),
        "avg_rating":       round(df['rating'].mean(), 2),
        "avg_score":        round(df['final_score'].mean(), 3),
        "top_aspect":       df['aspect'].mode()[0] if not df['aspect'].empty else "N/A",
    }

if __name__ == "__main__":
    from scraper import scrape_reviews
    df = scrape_reviews(url="", industry="FMCG", use_sample=True)
    results = run_full_analysis(df, "FMCG")
    print(results[['review_text', 'final_label', 'final_score', 'aspect']].to_string())
    print("\nSummary:", get_summary_stats(results))
    print("\nAlerts:", check_crisis(results))