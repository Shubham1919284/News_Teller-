import streamlit as st
import requests
import json
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from textblob import TextBlob
from datetime import datetime
import re

# ✅ Load API key securely from Streamlit Cloud secrets
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# Load country ISO codes from JSON
with open("countries_dict.json", "r") as f:
    country_codes = json.load(f)

def clean_text(text):
    return re.sub(r"\[\+\d+\schars\]", "", text).strip()

def summarize_text(text, sentence_count=2):
    try:
        text = clean_text(text)
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        summary_text = " ".join(str(sentence) for sentence in summary)
        words = summary_text.split()
        if len(words) > 200:
            summary_text = " ".join(words[:200]) + "..."
        return summary_text
    except:
        return "Summary not available"

def get_sentiments(text):
    try:
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.1:
            return "🟢 Positive"
        elif polarity < -0.1:
            return "🔴 Negative"
        else:
            return "🟡 Neutral"
    except:
        return "Unknown"

# --- Streamlit UI ---

st.set_page_config(page_title="News Digest App", layout="wide")
st.title("📰 News Digest with Summary & Sentiment")

country_name = st.selectbox("🌍 Select Country", list(country_codes.keys()), index=list(country_codes.keys()).index("India"))
country_code = country_codes.get(country_name, "IN")

query = st.text_input("🔍 Search Keyword")
category = st.selectbox("📂 Choose Category (Optional)", ["", "business", "entertainment", "general", "health", "science", "sports", "technology"])
action = st.radio("Action", ("Headlines", "Search", "Filter by Category"))

st.markdown("---")

articles = []
search_title = None

if action == "Search" and query:
    search_title = f'Search Results for "{query}" ({country_name})'
    url = f"https://newsapi.org/v2/everything?q={query}+{country_name}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
elif action == "Filter by Category" and category:
    search_title = f'Top News in Category: "{category.title()}" ({country_name})'
    url = f"https://newsapi.org/v2/top-headlines?country={country_code}&category={category}&language=en&apiKey={NEWS_API_KEY}"
else:
    search_title = f"Top News from {country_name}"
    url = f"https://newsapi.org/v2/top-headlines?country={country_code}&language=en&apiKey={NEWS_API_KEY}"

if url:
    response = requests.get(url)
    data = response.json()
    raw_articles = data.get("articles", [])

    # fallback if category fails
    if action == "Filter by Category" and not raw_articles:
        fallback_url = f"https://newsapi.org/v2/everything?q={category}+{country_name}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        response = requests.get(fallback_url)
        data = response.json()
        raw_articles = data.get("articles", [])

    raw_articles = raw_articles[:10]

    st.subheader(search_title)
    for item in raw_articles:
        raw_text = item.get("description") or item.get("content") or ""
        content = clean_text(raw_text)
        summary = summarize_text(content)
        sentiment = get_sentiments(content)

        source = item.get("source", {}).get("name", "Unknown Source")
        published = item.get("publishedAt", "")
        try:
            published_dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            published = published_dt.strftime("%d-%m-%Y %I:%M %p")
        except:
            published = "Unknown Time"

        st.markdown(f"### [{item.get('title', 'No Title')}]({item.get('url', '#')})")
        st.write(f"**Published:** {published} | **Source:** {source} | **Sentiment:** {sentiment}")
        st.write(f"📝 **Description:** {item.get('description', 'No description available')}")
        st.write(f"📌 **Summary:** {summary}")
        st.markdown("---")
