import streamlit as st
import requests
import json
import re
from datetime import datetime
from gensim.summarization import summarize
from textblob import TextBlob

with open("countries_dict.json", "r") as f:
    country_codes = json.load(f)

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

def clean_text(text):
    return re.sub(r"\[\+\d+\schars\]", "", text).strip()

def summarize_text(text, sentence_count=2):
    try:
        text = clean_text(text)
        if len(text.split()) < 30:
            return "Summary not available (content too short)."
        summary_text = summarize(text, word_count=200)
        return summary_text if summary_text else "Summary not available"
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
