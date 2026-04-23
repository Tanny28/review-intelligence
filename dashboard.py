import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from scraper import scrape_reviews
from nlp_engine import run_full_analysis, check_crisis, get_summary_stats
from report import generate_report
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
groq_key = (os.getenv("GROQ_API_KEY") or "").strip()

st.set_page_config(
    page_title="Review Intelligence System",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid #e0e0e0;
}
.alert-critical {
    background: #fff0f0;
    border-left: 4px solid #E24B4A;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
    color: #7a1a1a;
}
.alert-warning {
    background: #fffbf0;
    border-left: 4px solid #BA7517;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
    color: #7a4a00;
}
.review-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 14px;
    margin: 6px 0;
    border: 1px solid #e0e0e0;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 Enterprise Review Intelligence System")
st.caption("AI-powered customer feedback analysis for Banking, FMCG, Pharma & Fragrance industries")

st.markdown(
    "Turn review text into sentiment, aspects, crisis signals, an executive summary (Groq), and a downloadable PDF."
)


def render_ai_summary_from_text(summary: str) -> None:
    col_s1, col_s2 = st.columns(2)
    lines = summary.strip().split("\n")

    with col_s1:
        st.markdown("**Top Complaints**")
        in_complaints = False
        for line in lines:
            if "COMPLAINTS" in line:
                in_complaints = True
            elif "STRENGTHS" in line or "ACTION" in line:
                in_complaints = False
            elif in_complaints and line.startswith("- "):
                st.error(f"🔴 {line[2:]}")

    with col_s2:
        st.markdown("**Key Strengths**")
        in_strengths = False
        for line in lines:
            if "STRENGTHS" in line:
                in_strengths = True
            elif "ACTION" in line:
                in_strengths = False
            elif in_strengths and line.startswith("- "):
                st.success(f"🟢 {line[2:]}")

    for line in lines:
        if line.startswith("ACTION:"):
            st.info(f"💡 **Recommended Action:** {line[7:].strip()}")


with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=Review+Intelligence", width=200)
    st.markdown("---")

    st.subheader("⚙️ Configuration")

    industry = st.selectbox(
        "Select Industry",
        ["FMCG", "Banking", "Pharma", "Fragrance"],
        help="Each industry has custom NLP keywords and aspect categories"
    )

    st.markdown("---")
    st.subheader("🔗 Data Source")

    data_mode = st.radio(
        "Choose data mode",
        ["Sample Data (Demo)", "Enter URL"],
        help="Sample data works instantly. URL scraping attempts live fetch."
    )

    url = ""
    if data_mode == "Enter URL":
        url = st.text_input("Business URL", placeholder="https://www.example.com/reviews")

    st.markdown("---")

    compare_mode = st.checkbox("Enable Competitor Comparison")
    url2 = ""
    industry2 = industry
    if compare_mode:
        st.subheader("🆚 Competitor")
        url2 = st.text_input("Competitor URL", placeholder="https://competitor.com/reviews")
        industry2 = st.selectbox("Competitor Industry", ["FMCG", "Banking", "Pharma", "Fragrance"], key="ind2")

    st.markdown("---")

    if groq_key:
        st.success("🔑 Groq API key loaded", icon="✅")
    else:
        st.warning("⚠️ No GROQ_API_KEY in .env — AI summaries disabled.")

    analyze_btn = st.button("🚀 Analyze Reviews", use_container_width=True, type="primary")

# ── Run analysis only when Analyze is clicked; keep results in session for other widgets ──
if analyze_btn:
    st.session_state.pop("review_intel_pdf", None)
    st.session_state.pop("review_intel_pdf_name", None)

    if data_mode == "Enter URL" and not url.strip():
        st.error("Enter a business URL before clicking Analyze Reviews.")
        st.stop()

    with st.spinner(f"Fetching and analyzing {industry} reviews..."):
        use_sample = data_mode == "Sample Data (Demo)"
        df_raw = scrape_reviews(url=url, industry=industry, use_sample=use_sample)
        df = run_full_analysis(df_raw, industry)

    alerts = check_crisis(df)
    stats = get_summary_stats(df)

    ai_summary_for_report = None
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            neg_reviews = df[df["final_label"] == "Negative"]["review_text"].head(10).tolist()
            pos_reviews = df[df["final_label"] == "Positive"]["review_text"].head(5).tolist()
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
            with st.spinner("Generating AI summary..."):
                chat = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                )
                ai_summary_for_report = chat.choices[0].message.content
        except Exception as e:
            err_lower = str(e).lower()
            if (
                "401" in str(e)
                or "invalid_api_key" in err_lower
                or "incorrect api key" in err_lower
                or "unauthorized" in err_lower
            ):
                st.error(
                    "Groq API key is missing or invalid. Update `GROQ_API_KEY` in your `.env` file and reload."
                )
            else:
                st.warning(f"AI summary unavailable: {e}")

    stats2 = None
    industry2_saved = None
    if compare_mode and (url2 or data_mode == "Sample Data (Demo)"):
        with st.spinner("Analyzing competitor..."):
            use_sample2 = data_mode == "Sample Data (Demo)"
            df_raw2 = scrape_reviews(url=url2, industry=industry2, use_sample=use_sample2)
            df2 = run_full_analysis(df_raw2, industry2)
            stats2 = get_summary_stats(df2)
        industry2_saved = industry2

    st.session_state["review_df"] = df
    st.session_state["review_stats"] = stats
    st.session_state["review_alerts"] = alerts
    st.session_state["review_industry"] = industry
    st.session_state["review_ai_summary"] = ai_summary_for_report
    st.session_state["review_compare_mode"] = compare_mode
    st.session_state["review_stats2"] = stats2
    st.session_state["review_industry2"] = industry2_saved
    st.session_state["review_generated_at"] = datetime.now().isoformat(timespec="seconds")

    st.success(f"Analyzed {len(df)} reviews successfully!")
    st.markdown("---")

# ── Show results whenever we have a stored analysis (survives PDF / filter / download clicks) ──
if st.session_state.get("review_df") is not None:
    df = st.session_state["review_df"]
    stats = st.session_state["review_stats"]
    alerts = st.session_state["review_alerts"]
    report_industry = st.session_state["review_industry"]
    ai_summary_for_report = st.session_state.get("review_ai_summary")
    compare_mode_saved = st.session_state.get("review_compare_mode", False)
    stats2 = st.session_state.get("review_stats2")
    industry2_saved = st.session_state.get("review_industry2")

    if industry != report_industry:
        st.info(
            "Sidebar industry does not match the loaded results. Click **Analyze Reviews** to refresh."
        )

    generated_at = st.session_state.get("review_generated_at")
    if generated_at:
        st.caption(f"Last analysis run: {generated_at}")

    if alerts:
        st.subheader("🚨 Crisis Alerts")
        for alert in alerts:
            css_class = "alert-critical" if alert["type"] == "CRITICAL" else "alert-warning"
            st.markdown(
                f'<div class="{css_class}">{alert["icon"]} <strong>{alert["type"]}:</strong> {alert["message"]}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("---")
    else:
        st.info("No crisis alerts triggered for this run.")
        st.markdown("---")

    st.subheader("📊 Overview")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Reviews", stats["total_reviews"])
    with col2:
        st.metric("Positive", f"{stats['positive_pct']}%", delta=None)
    with col3:
        st.metric("Negative", f"{stats['negative_pct']}%", delta=None)
    with col4:
        st.metric("Avg Rating", f"{stats['avg_rating']}/5")
    with col5:
        st.metric("Top Issue", stats["top_aspect"])

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💬 Sentiment Distribution")
        sentiment_counts = df["final_label"].value_counts().reset_index()
        sentiment_counts.columns = ["Sentiment", "Count"]
        colors = {"Positive": "#1D9E75", "Negative": "#E24B4A", "Neutral": "#BA7517"}
        fig_pie = px.pie(
            sentiment_counts,
            values="Count",
            names="Sentiment",
            color="Sentiment",
            color_discrete_map=colors,
            hole=0.4,
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("🏷️ Aspect Breakdown")
        aspect_counts = df["aspect"].value_counts().reset_index()
        aspect_counts.columns = ["Aspect", "Count"]
        fig_bar = px.bar(
            aspect_counts,
            x="Count",
            y="Aspect",
            orientation="h",
            color="Count",
            color_continuous_scale="teal",
        )
        fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📈 Sentiment Trend Over Time")
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["date"])
    trend = df_plot.groupby("date")["final_score"].mean().reset_index()
    fig_trend = px.line(
        trend,
        x="date",
        y="final_score",
        markers=True,
        line_shape="spline",
    )
    fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral line")
    fig_trend.update_traces(line_color="#534AB7", marker_color="#534AB7")
    fig_trend.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=280,
        xaxis_title="Date",
        yaxis_title="Avg Sentiment Score",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    st.subheader("🤖 AI Executive Summary")
    if ai_summary_for_report:
        st.caption("AI summary included in the PDF export below.")
        render_ai_summary_from_text(ai_summary_for_report)
    elif groq_key:
        st.warning(
            "AI summary was not generated for this run. Click **Analyze Reviews** to regenerate."
        )
    else:
        st.info("💡 Add `GROQ_API_KEY=your_key` to a `.env` file in your project root to unlock AI summaries.")

    st.markdown("---")

    if compare_mode_saved and stats2 is not None and industry2_saved is not None:
        st.subheader("🆚 Competitor Comparison")
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown(f"**Your Brand ({report_industry})**")
            st.metric("Positive", f"{stats['positive_pct']}%")
            st.metric("Avg Rating", f"{stats['avg_rating']}/5")
            st.metric("Negative", f"{stats['negative_pct']}%")

        with col_c2:
            st.markdown(f"**Competitor ({industry2_saved})**")
            st.metric("Positive", f"{stats2['positive_pct']}%")
            st.metric("Avg Rating", f"{stats2['avg_rating']}/5")
            st.metric("Negative", f"{stats2['negative_pct']}%")
    elif compare_mode_saved:
        st.info("Competitor comparison data isn't available yet. Click **Analyze Reviews** to refresh.")

    st.markdown("---")
    st.subheader("📝 Individual Reviews")
    filter_sentiment = st.selectbox("Filter by sentiment", ["All", "Positive", "Negative", "Neutral"])

    filtered = df if filter_sentiment == "All" else df[df["final_label"] == filter_sentiment]

    for _, row in filtered.head(10).iterrows():
        st.markdown(f"""
        <div class="review-card">
            <strong>{row['emoji']} {row['final_label']}</strong> &nbsp;|&nbsp;
            Score: <strong>{row['final_score']}</strong> &nbsp;|&nbsp;
            Aspect: <strong>{row['aspect']}</strong> &nbsp;|&nbsp;
            Rating: {'⭐' * int(row['rating'])}<br>
            <span style="color:#555; font-size:14px">{row['review_text']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📄 Export Report")
    st.caption(
        "PDF includes executive overview, crisis alerts (if any), tables (sentiment + aspects), optional AI summary, and sample reviews."
    )

    if st.button("⬇️ Download PDF Report", use_container_width=True, key="gen_review_pdf"):
        try:
            with st.spinner("Generating PDF..."):
                buffer = generate_report(
                    df=df,
                    stats=stats,
                    alerts=alerts,
                    industry=report_industry,
                    ai_summary=ai_summary_for_report,
                )
                st.session_state["review_intel_pdf"] = buffer.getvalue()
                st.session_state["review_intel_pdf_name"] = (
                    f"review_report_{report_industry}_{datetime.now().strftime('%Y%m%d')}.pdf"
                )
            st.success("PDF ready — use the download button below.")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

    if st.session_state.get("review_intel_pdf"):
        st.download_button(
            label="📥 Click here to download",
            data=st.session_state["review_intel_pdf"],
            file_name=st.session_state.get(
                "review_intel_pdf_name",
                f"review_report_{report_industry}_{datetime.now().strftime('%Y%m%d')}.pdf",
            ),
            mime="application/pdf",
            key="dl_review_pdf",
        )

else:
    st.markdown("---")
    st.markdown("""
    ### 👈 Get Started
    1. Select your **industry** from the sidebar
    2. Choose **Sample Data** for instant demo
    3. Hit **Analyze Reviews**
    4. Set `GROQ_API_KEY` in `.env` for Groq-powered summaries
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("🏦 **Banking**\nFees, service, digital experience")
    with col2:
        st.success("🛒 **FMCG**\nQuality, delivery, packaging")
    with col3:
        st.warning("💊 **Pharma**\nEfficacy, side effects, pricing")
    with col4:
        st.error("🌸 **Fragrance**\nLongevity, scent, value")
