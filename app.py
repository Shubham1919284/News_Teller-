import streamlit as st
import requests
import json
import pandas as pd
from gensim.summarization import summarize
from datetime import datetime

# ---------------------- News Fetching Logic ----------------------

@st.cache_data(show_spinner=False)
def load_countries():
    with open("countries_dict.json", "r") as f:
        return json.load(f)

@st.cache_data(ttl=3600)
def fetch_news(country_code, category=None):
    base_url = "https://newsapi.org/v2/top-headlines"
    api_key = st.secrets["news_api_key"]
    params = {"country": country_code, "apiKey": api_key, "pageSize": 100}
    if category:
        params["category"] = category
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return pd.DataFrame(articles)
    else:
        return pd.DataFrame()

# ---------------------- Summarization Logic ----------------------

def clean_text(text):
    return text.replace("\n", " ").replace("\xa0", " ").strip()

def summarize_text(text, ratio=0.2):
    try:
        text = clean_text(text)
        if len(text.split('.')) < 10 or len(text) < 500:
            return "Summary not available (text too short)."
        summary = summarize(text, ratio=ratio)
        if not summary.strip():
            return "Summary not available"
        return summary
    except Exception as e:
        st.error(f"❌ Summary error: {e}")
        return "Summary not available"

# ---------------------- Streamlit App UI ----------------------

def render_article(article):
    st.subheader(article["title"])
    st.write(f"**Source:** {article['source']['name']} | **Published:** {article['publishedAt'][:10]}")
    if article.get("urlToImage"):
        st.image(article["urlToImage"], use_column_width=True)
    st.write(article.get("description") or "No description available")
    st.markdown(f"[Read Full Article]({article['url']})")

    if article.get("content"):
        with st.expander("🔍 Show Summary"):
            summary = summarize_text(article["content"])
            st.write(summary)
    st.markdown("---")

# ---------------------- App Execution ----------------------

def main():
    st.set_page_config(page_title="News Digest", layout="centered")
    st.title("🗞️ News Digest App")

    countries = load_countries()
    country_name = st.selectbox("🌍 Select a Country", list(countries.keys()), index=13)
    category = st.selectbox("🗂️ Select Category (Optional)", ["", "business", "entertainment", "health", "science", "sports", "technology"])

    news_df = fetch_news(countries[country_name], category if category else None)

    if not news_df.empty:
        st.success(f"✅ Found {len(news_df)} articles")
        for _, article in news_df.iterrows():
            render_article(article)
    else:
        st.warning("No news articles found.")

if __name__ == "__main__":
    main()
