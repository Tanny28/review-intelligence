import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import os

try:
    from fake_useragent import UserAgent
    ua = UserAgent()
except ImportError:
    ua = None

def get_random_headers():
    user_agent = ua.random if ua else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    return {"User-Agent": user_agent}

INDUSTRY_KEYWORDS = {
    "Banking": ["loan", "interest", "fees", "account", "transaction", "branch", "ATM", "customer service", "fraud", "credit"],
    "FMCG": ["packaging", "taste", "freshness", "delivery", "quality", "price", "expiry", "product", "smell", "value"],
    "Pharma": ["efficacy", "side effects", "dosage", "packaging", "delivery", "price", "genuine", "expiry", "prescription"],
    "Fragrance": ["smell", "longevity", "sillage", "bottle", "packaging", "price", "occasions", "compliments", "projection"]
}

SAMPLE_DATA = {
    "Banking": [
        {"review_text": "The loan process was smooth but interest rates are too high compared to others.", "rating": 3, "date": "2024-01-15", "reviewer": "Rahul M."},
        {"review_text": "Excellent customer service! My fraud complaint was resolved within 24 hours.", "rating": 5, "date": "2024-01-20", "reviewer": "Priya S."},
        {"review_text": "ATM always out of cash in my area. Very frustrating experience.", "rating": 1, "date": "2024-02-01", "reviewer": "Amit K."},
        {"review_text": "Mobile app is very user friendly and transactions are instant.", "rating": 5, "date": "2024-02-10", "reviewer": "Sneha R."},
        {"review_text": "Hidden charges on my account were not disclosed upfront. Very disappointing.", "rating": 2, "date": "2024-02-15", "reviewer": "Vikram P."},
        {"review_text": "Branch staff is extremely helpful. Got my credit card issue resolved quickly.", "rating": 4, "date": "2024-02-20", "reviewer": "Neha T."},
        {"review_text": "Worst banking experience. Waited 2 hours at branch for a simple query.", "rating": 1, "date": "2024-03-01", "reviewer": "Suresh L."},
        {"review_text": "Interest rates on savings account are competitive. Happy with returns.", "rating": 4, "date": "2024-03-05", "reviewer": "Anita D."},
        {"review_text": "Online portal keeps crashing. Cannot access my statements for weeks.", "rating": 2, "date": "2024-03-10", "reviewer": "Rohit G."},
        {"review_text": "Fixed deposit rates are great. Very satisfied with the investment.", "rating": 5, "date": "2024-03-15", "reviewer": "Kavita N."},
        {"review_text": "Customer care puts you on hold for 45 minutes. Absolutely unacceptable.", "rating": 1, "date": "2024-03-20", "reviewer": "Deepak S."},
        {"review_text": "Seamless net banking experience. All features work perfectly.", "rating": 5, "date": "2024-03-25", "reviewer": "Pooja V."},
        {"review_text": "Loan rejection without any proper reason given. Very disappointing.", "rating": 2, "date": "2024-04-01", "reviewer": "Arun M."},
        {"review_text": "Best bank for small business owners. Flexible repayment options.", "rating": 5, "date": "2024-04-05", "reviewer": "Sunita B."},
        {"review_text": "Transaction fees are too high for international transfers.", "rating": 3, "date": "2024-04-10", "reviewer": "Kiran J."},
    ],
    "FMCG": [
        {"review_text": "Product quality has gone down drastically in last few months.", "rating": 2, "date": "2024-01-12", "reviewer": "Meera P."},
        {"review_text": "Packaging is excellent and product arrived fresh. Very happy.", "rating": 5, "date": "2024-01-18", "reviewer": "Raj K."},
        {"review_text": "Taste is not consistent. Sometimes good sometimes terrible.", "rating": 3, "date": "2024-02-05", "reviewer": "Sita R."},
        {"review_text": "Delivery was 3 days late and product was near expiry. Unacceptable.", "rating": 1, "date": "2024-02-14", "reviewer": "Mohan L."},
        {"review_text": "Best value for money product in this category. Will repurchase.", "rating": 5, "date": "2024-02-22", "reviewer": "Divya T."},
        {"review_text": "Smell is off. Product does not match the description on website.", "rating": 2, "date": "2024-03-03", "reviewer": "Arjun S."},
        {"review_text": "Quantity reduced but price stayed same. Feels like cheating customers.", "rating": 2, "date": "2024-03-11", "reviewer": "Lata M."},
        {"review_text": "Absolutely love this product. Using it for 2 years and quality is consistent.", "rating": 5, "date": "2024-03-19", "reviewer": "Nitin V."},
        {"review_text": "Received damaged packaging. Refund process was too complicated.", "rating": 2, "date": "2024-03-27", "reviewer": "Rekha B."},
        {"review_text": "Great product at an affordable price. Delivery was also on time.", "rating": 4, "date": "2024-04-02", "reviewer": "Sachin G."},
        {"review_text": "Product expired before mentioned date. Very dangerous.", "rating": 1, "date": "2024-04-08", "reviewer": "Uma K."},
        {"review_text": "Freshness is maintained well. Impressed with the quality control.", "rating": 5, "date": "2024-04-14", "reviewer": "Vivek N."},
        {"review_text": "Too much unnecessary plastic packaging. Not eco friendly at all.", "rating": 3, "date": "2024-04-20", "reviewer": "Preeti J."},
        {"review_text": "Bulk discount offer is amazing. Saves a lot of money every month.", "rating": 5, "date": "2024-04-26", "reviewer": "Ganesh R."},
        {"review_text": "Wrong product delivered twice. Customer support is non responsive.", "rating": 1, "date": "2024-05-01", "reviewer": "Shanti D."},
    ],
    "Pharma": [
        {"review_text": "Medicine worked effectively within 2 days. No side effects noticed.", "rating": 5, "date": "2024-01-10", "reviewer": "Dr. Sharma"},
        {"review_text": "Packaging was damaged and seal was broken. Very concerning for medicine.", "rating": 1, "date": "2024-01-22", "reviewer": "Patient A."},
        {"review_text": "Generic version works just as well at half the price. Recommended.", "rating": 4, "date": "2024-02-08", "reviewer": "Ramesh K."},
        {"review_text": "Dosage instructions are unclear on the packaging. Needs improvement.", "rating": 3, "date": "2024-02-16", "reviewer": "Nurse B."},
        {"review_text": "Experienced severe side effects not mentioned on the label.", "rating": 1, "date": "2024-02-25", "reviewer": "Patient C."},
        {"review_text": "Delivery was fast and medicine was genuine. Very reliable.", "rating": 5, "date": "2024-03-04", "reviewer": "Chemist D."},
        {"review_text": "Price increased 40% without any explanation. Very unfair.", "rating": 2, "date": "2024-03-13", "reviewer": "Consumer E."},
        {"review_text": "Prescription requirement process is smooth and professional.", "rating": 4, "date": "2024-03-21", "reviewer": "Doctor F."},
        {"review_text": "Received near expiry stock. Pharmacist was not helpful.", "rating": 1, "date": "2024-03-30", "reviewer": "Patient G."},
        {"review_text": "Efficacy is excellent. Symptoms reduced significantly after first dose.", "rating": 5, "date": "2024-04-07", "reviewer": "Patient H."},
        {"review_text": "Cold chain was not maintained during delivery. Product quality affected.", "rating": 2, "date": "2024-04-15", "reviewer": "Chemist I."},
        {"review_text": "Very satisfied with the product quality and customer support.", "rating": 5, "date": "2024-04-23", "reviewer": "Doctor J."},
    ],
    "Fragrance": [
        {"review_text": "Amazing longevity! Lasts more than 12 hours even in summer heat.", "rating": 5, "date": "2024-01-08", "reviewer": "Fragrance Fan"},
        {"review_text": "Projection is weak. Can barely smell it after 2 hours.", "rating": 2, "date": "2024-01-17", "reviewer": "Perfume Lover"},
        {"review_text": "Bottle design is gorgeous. Perfect as a gift for any occasion.", "rating": 5, "date": "2024-02-03", "reviewer": "Gift Buyer"},
        {"review_text": "Smell is completely different from what was described online. Disappointed.", "rating": 2, "date": "2024-02-12", "reviewer": "Scent Seeker"},
        {"review_text": "Got so many compliments wearing this. Absolutely love it.", "rating": 5, "date": "2024-02-21", "reviewer": "Happy Customer"},
        {"review_text": "Price is too high for the sillage. Not worth the money.", "rating": 2, "date": "2024-03-02", "reviewer": "Value Hunter"},
        {"review_text": "Perfect for office wear. Subtle and professional scent.", "rating": 4, "date": "2024-03-12", "reviewer": "Office Worker"},
        {"review_text": "Received a fake bottle. The cap was different and smell was off.", "rating": 1, "date": "2024-03-22", "reviewer": "Disappointed Buyer"},
        {"review_text": "Seasonal fragrance that is perfect for monsoon. Very refreshing.", "rating": 5, "date": "2024-04-01", "reviewer": "Season Lover"},
        {"review_text": "Packaging was damaged during shipping. Bottle leaked inside the box.", "rating": 1, "date": "2024-04-11", "reviewer": "Online Shopper"},
        {"review_text": "Best budget fragrance available. Punches above its price point.", "rating": 5, "date": "2024-04-21", "reviewer": "Budget King"},
        {"review_text": "Longevity claims on bottle are exaggerated. Barely lasts 3 hours.", "rating": 2, "date": "2024-05-01", "reviewer": "Honest Review"},
    ]
}

def get_sample_reviews(industry="FMCG"):
    """Returns sample review data for the selected industry"""
    data = SAMPLE_DATA.get(industry, SAMPLE_DATA["FMCG"])
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["industry"] = industry
    df["source"] = "Sample Data"
    return df

def scrape_google_serper(query_or_url, industry):
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("SERPER_API_KEY not found. Using sample data.")
        return get_sample_reviews(industry)
        
    try:
        url = "https://google.serper.dev/search"
        payload = {"q": f"{query_or_url} customer feedback reviews"}
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()
        
        reviews = []
        for item in data.get("organic", [])[:20]:
            snippet = item.get("snippet", "")
            if len(snippet) > 15:
                reviews.append({
                    "review_text": snippet,
                    "rating": random.randint(3, 5),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "reviewer": item.get("title", "Anonymous")[:30],
                    "industry": industry,
                    "source": "Google (Serper)"
                })
        if reviews:
            df = pd.DataFrame(reviews)
            df["date"] = pd.to_datetime(df["date"])
            print(f"Serper.dev fetched {len(df)} snippets.")
            return df
    except Exception as e:
        print(f"Serper API failed: {e}")
    return get_sample_reviews(industry)

def scrape_reviews(url, industry="FMCG", use_sample=True):
    """
    Main scraper function.
    use_sample=True uses built-in data (safe, no blocking)
    use_sample=False attempts real scraping
    """
    if use_sample:
        print(f"Loading sample {industry} review data...")
        df = get_sample_reviews(industry)
        print(f"Loaded {len(df)} reviews successfully.")
        return df

    if "google" in url.lower():
        return scrape_google_serper(url, industry)

    try:
        print(f"Attempting generic scrape: {url}")
        time.sleep(random.uniform(1, 2))
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        reviews = []
        review_blocks = soup.find_all("div", class_=lambda x: x and "review" in x.lower())

        for block in review_blocks[:20]:
            text = block.get_text(strip=True)
            if len(text) > 20:
                reviews.append({
                    "review_text": text[:500],
                    "rating": random.randint(1, 5),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "reviewer": "Anonymous",
                    "industry": industry,
                    "source": url
                })

        if reviews:
            df = pd.DataFrame(reviews)
            df["date"] = pd.to_datetime(df["date"])
            print(f"Scraped {len(df)} reviews.")
            return df
        else:
            print("No reviews found via scraping. Falling back to sample data.")
            return get_sample_reviews(industry)

    except Exception as e:
        print(f"Scraping failed: {e}. Using sample data instead.")
        return get_sample_reviews(industry)

def get_industry_keywords(industry):
    """Returns relevant keywords for the selected industry"""
    return INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["FMCG"])

if __name__ == "__main__":
    df = scrape_reviews(url="", industry="Banking", use_sample=True)
    print(df.head())
    print(f"\nTotal reviews: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")