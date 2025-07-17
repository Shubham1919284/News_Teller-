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

nltk.download("punkt")

with open("countries_dict.json", "r") as f:
    country_codes = json.load(f)

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

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
    except Exception as e:
        print("Summary error:", e)
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

st.set_page_config(page_title="Smart News Digest", layout="wide")
st.title("📰 Smart News Digest")
st.markdown("Get summarized and sentiment-analyzed news by country, category, or keyword.")

with st.sidebar:
    st.header("🔍 Filter Options")
    query = st.text_input("Search News")
    category = st.selectbox("Select Category", ["", "business", "entertainment", "general", "health", "science", "sports", "technology"])
    country = st.selectbox("Select Country", list(country_codes.keys()), index=list(country_codes.keys()).index("India"))
    action = st.radio("Action", ["Top Headlines", "Search", "Filter by Category"])

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

response = requests.get(url)
data = response.json()
raw_articles = data.get("articles", [])

if action == "Filter by Category" and not raw_articles:
    fallback_url = f"https://newsapi.org/v2/everything?q={category}+{country}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    response = requests.get(fallback_url)
    data = response.json()
    raw_articles = data.get("articles", [])

raw_articles = raw_articles[:10]

st.subheader(search_title)
if not raw_articles:
    st.warning("No articles found.")
else:
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

        with st.expander(item.get("title", "No Title")):
            st.markdown(f"**🗞️ Source:** {source}  **🕒 Published:** {published}")
            st.markdown(f"**📌 Description:** {item.get('description', 'No description')}")
            st.markdown(f"**📝 Summary:** {summary}")
            st.markdown(f"**📈 Sentiment:** {sentiment}")
            st.markdown(f"[🔗 Read Full Article]({item.get('url', '#')})")
