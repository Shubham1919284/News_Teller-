import streamlit as st
import requests
import json
import re
from datetime import datetime
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from textblob import TextBlob
import nltk
import os

# ✅ Use local nltk_data folder
nltk.data.path.append("./nltk_data")
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    st.error("❌ 'punkt' tokenizer not found. Please include the 'nltk_data' folder with 'punkt' in your project.")

# Load country codes
with open("countries_dict.json", "r") as f:
    country_codes = json.load(f)

# API key from secrets
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# Clean article content
def clean_text(text):
    return re.sub(r"\[\+\d+\schars\]", "", text).strip()

# Text summarizer
def summarize_text(text, sentence_count=2):
    try:
        text = clean_text(text)
        if len(text.split()) < 30:
            return "Summary not available (content too short)."
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        summary_text = " ".join(str(sentence) for sentence in summary)
        words = summary_text.split()
        if len(words) > 200:
            summary_text = " ".join(words[:200]) + "..."
        return summary_text if summary_text else "Summary not available"
    except Exception as e:
        st.error(f"❌ Summary error: {e}")
        return "Summary not available"

# Sentiment analyzer
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
        return "⚪ Unknown"

# Streamlit setup
st.set_page_config(page_title="Smart News Digest", layout="wide")
st.title("📰 Smart News Digest")
st.markdown("Get summarized and sentiment-analyzed news by country, category, or keyword.")

# Sidebar
with st.sidebar:
    st.header("🔍 Filter Options")
    query = st.text_input("Search News")
    category = st.selectbox("Select Category", ["", "business", "entertainment", "general", "health", "science", "sports", "technology"])
    country = st.selectbox("Select Country", list(country_codes.keys()), index=list(country_codes.keys()).index("India"))
    action = st.radio("Action", ["Top Headlines", "Search", "Filter by Category"])

# Build API URL
country_code = country_codes.get(country, "IN")
articles = []
search_title = ""

if action == "Search" and query:
    search_title = f'Search Results for "{query}" ({country})'
    url = f"https://newsapi.org/v2/everything?q={query}+{country}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
elif action == "Filter by Category" and category:
    search_title = f'Top News in Category: "{category.title()}" ({country})'
    url = f"https://newsapi.org/v2/top-headlines?country={country_code}&category={category}&language=en&apiKey={NEWS_API_KEY}"
else:
    search_title = f"Top Headlines in {country}"
    url = f"https://newsapi.org/v2/top-headlines?country={country_code}&language=en&apiKey={NEWS_API_KEY}"

# Fetch articles
response = requests.get(url)
data = response.json()
raw_articles = data.get("articles", [])

# Fallback for category if no results
if action == "Filter by Category" and not raw_articles:
    fallback_url = f"https://newsapi.org/v2/everything?q={category}+{country}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    response = requests.get(fallback_url)
    data = response.json()
    raw_articles = data.get("articles", [])

raw_articles = raw_articles[:10]  # show only top 10

# Display articles
st.subheader(search_title)
if not raw_articles:
    st.warning("No articles found.")
else:
    for item in raw_articles:
        title = item.get("title", "")
        description = item.get("description", "")
        content_raw = item.get("content", "")

        combined_text = f"{title}. {description} {content_raw}".strip()
        content = clean_text(combined_text)

        summary = summarize_text(content)
        sentiment = get_sentiments(content)

        source = item.get("source", {}).get("name", "Unknown Source")
        published = item.get("publishedAt", "")
        try:
            published_dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            published = published_dt.strftime("%d-%m-%Y %I:%M %p")
        except:
            published = "Unknown Time"

        with st.expander(title or "No Title"):
            st.markdown(f"**🗞️ Source:** {source}  **🕒 Published:** {published}")
            st.markdown(f"**📌 Description:** {description or 'No description'}")
            st.markdown(f"**📝 Summary:** {summary}")
            st.markdown(f"**📈 Sentiment:** {sentiment}")
            st.markdown(f"[🔗 Read Full Article]({item.get('url', '#')})")
