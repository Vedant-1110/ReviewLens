import os
import re
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

import scraper
import analysis


# ============================================================
# CONFIGURATION
# ============================================================

DATA_FILE = "data/scraped_reviews.csv"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ReviewLens",
    page_icon="⭐",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        color: #777;
        font-size: 1rem;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">⭐ ReviewLens</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Restaurant Review Scraping & Analytics Dashboard'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR - SCRAPER
# ============================================================

st.sidebar.title("🔎 ReviewLens")

st.sidebar.subheader(
    "Collect New Reviews"
)

search_query = st.sidebar.text_input(
    "Google Maps Search",
    value="restaurants in Vadodara"
)

max_reviews = st.sidebar.number_input(
    "Maximum Reviews",
    min_value=10,
    max_value=500,
    value=100,
    step=10
)

start_scraping = st.sidebar.button(
    "🚀 Start Scraping",
    use_container_width=True
)


# ============================================================
# SCRAPE + ANALYZE
# ============================================================

if start_scraping:

    if not search_query.strip():

        st.sidebar.error(
            "Please enter a search query."
        )

    else:

        with st.status(
            "Running ReviewLens...",
            expanded=True
        ) as status:

            try:

                st.write(
                    "🌐 Opening Google Maps..."
                )

                reviews = scraper.main(
                    search_query.strip(),
                    int(max_reviews)
                )

                if not reviews:

                    status.update(
                        label="No reviews collected.",
                        state="error"
                    )

                    st.error(
                        "No reviews were collected."
                    )

                    st.stop()

                st.write(
                    f"✅ Collected "
                    f"{len(reviews)} reviews."
                )

                st.write(
                    "📊 Running data analysis..."
                )

                analysis.run_analysis()

                st.write(
                    "✅ Analysis completed."
                )

                status.update(
                    label="ReviewLens completed successfully!",
                    state="complete"
                )

                st.cache_data.clear()

                st.rerun()

            except Exception as e:

                status.update(
                    label="ReviewLens failed.",
                    state="error"
                )

                st.error(
                    f"Error: {e}"
                )


# ============================================================
# CHECK DATA
# ============================================================

if not os.path.exists(DATA_FILE):

    st.info(
        "👈 Enter a Google Maps search query "
        "and click **🚀 Start Scraping** to begin."
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    return pd.read_csv(
        DATA_FILE
    )


df = load_data()


# ============================================================
# CLEAN DATA
# ============================================================

df = df.dropna(
    how="all"
).copy()

df["rating"] = pd.to_numeric(
    df["rating"],
    errors="coerce"
)

df = df[
    df["rating"].between(1, 5)
].copy()

for column in [
    "business_name",
    "author_name",
    "text",
    "review_date"
]:

    if column in df.columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
        )


# ============================================================
# SENTIMENT
# ============================================================

def rating_sentiment(rating):

    if rating >= 4:
        return "Positive"

    elif rating == 3:
        return "Neutral"

    return "Negative"


df["sentiment"] = (
    df["rating"]
    .apply(rating_sentiment)
)


# ============================================================
# REVIEW METRICS
# ============================================================

df["review_length"] = (
    df["text"]
    .str.len()
)

df["word_count"] = (
    df["text"]
    .str.split()
    .str.len()
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.divider()

st.sidebar.subheader(
    "Dashboard Filters"
)

restaurants = sorted(
    df["business_name"]
    .unique()
)

selected_restaurant = st.sidebar.selectbox(
    "Restaurant",
    ["All Restaurants"] + restaurants
)

selected_ratings = st.sidebar.multiselect(
    "Rating",
    [1, 2, 3, 4, 5],
    default=[1, 2, 3, 4, 5]
)

selected_sentiments = st.sidebar.multiselect(
    "Sentiment",
    [
        "Positive",
        "Neutral",
        "Negative"
    ],
    default=[
        "Positive",
        "Neutral",
        "Negative"
    ]
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df[
    df["rating"].isin(
        selected_ratings
    )
]

filtered_df = filtered_df[
    filtered_df["sentiment"].isin(
        selected_sentiments
    )
]

if selected_restaurant != "All Restaurants":

    filtered_df = filtered_df[
        filtered_df["business_name"]
        == selected_restaurant
    ]


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_reviews = len(
    filtered_df
)

average_rating = (
    filtered_df["rating"].mean()
    if total_reviews > 0
    else 0
)

positive_reviews = len(
    filtered_df[
        filtered_df["sentiment"]
        == "Positive"
    ]
)

neutral_reviews = len(
    filtered_df[
        filtered_df["sentiment"]
        == "Neutral"
    ]
)

negative_reviews = len(
    filtered_df[
        filtered_df["sentiment"]
        == "Negative"
    ]
)


# ============================================================
# OVERVIEW
# ============================================================

st.subheader(
    "📊 Overview"
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Reviews",
    total_reviews
)

col2.metric(
    "Average Rating",
    f"{average_rating:.2f} ⭐"
)

col3.metric(
    "Positive",
    positive_reviews
)

col4.metric(
    "Neutral",
    neutral_reviews
)

col5.metric(
    "Negative",
    negative_reviews
)


st.divider()


# ============================================================
# RATING DISTRIBUTION
# ============================================================

st.subheader(
    "⭐ Rating Distribution"
)

rating_counts = (
    filtered_df["rating"]
    .value_counts()
    .sort_index()
    .reset_index()
)

rating_counts.columns = [
    "rating",
    "count"
]

fig_rating = px.bar(
    rating_counts,
    x="rating",
    y="count",
    text="count",
    title="Number of Reviews by Rating",
    labels={
        "rating": "Rating",
        "count": "Reviews"
    }
)

fig_rating.update_traces(
    textposition="outside"
)

fig_rating.update_xaxes(
    dtick=1
)

st.plotly_chart(
    fig_rating,
    use_container_width=True
)


# ============================================================
# SENTIMENT
# ============================================================

st.subheader(
    "😊 Sentiment Analysis"
)

col1, col2 = st.columns(2)

sentiment_counts = (
    filtered_df["sentiment"]
    .value_counts()
    .reset_index()
)

sentiment_counts.columns = [
    "sentiment",
    "count"
]


with col1:

    fig_pie = px.pie(
        sentiment_counts,
        names="sentiment",
        values="count",
        hole=0.4,
        title="Sentiment Distribution"
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )


with col2:

    fig_sentiment = px.bar(
        sentiment_counts,
        x="sentiment",
        y="count",
        text="count",
        title="Sentiment Count"
    )

    fig_sentiment.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_sentiment,
        use_container_width=True
    )


# ============================================================
# REVIEW LENGTH
# ============================================================

st.subheader(
    "📝 Review Text Analysis"
)

col1, col2 = st.columns(2)


with col1:

    fig_length = px.box(
        filtered_df,
        x="rating",
        y="review_length",
        title="Review Length by Rating",
        labels={
            "rating": "Rating",
            "review_length": "Characters"
        }
    )

    st.plotly_chart(
        fig_length,
        use_container_width=True
    )


with col2:

    fig_word_count = px.scatter(
        filtered_df,
        x="rating",
        y="word_count",
        hover_data=[
            "business_name",
            "review_date"
        ],
        title="Rating vs Word Count",
        labels={
            "rating": "Rating",
            "word_count": "Words"
        }
    )

    st.plotly_chart(
        fig_word_count,
        use_container_width=True
    )


# ============================================================
# TOP WORDS
# ============================================================

st.subheader(
    "🔤 Most Common Words"
)


def get_top_words(
    texts,
    top_n=20
):

    stop_words = {
        "the",
        "and",
        "was",
        "were",
        "this",
        "that",
        "with",
        "for",
        "have",
        "had",
        "very",
        "good",
        "great",
        "you",
        "but",
        "are",
        "our",
        "they",
        "from",
        "restaurant",
        "food",
        "here",
        "not",
        "all",
        "too",
        "its",
        "their",
        "also",
        "has",
        "been",
        "there",
        "what",
        "which",
        "would",
        "could",
        "about",
        "just"
    }

    words = []

    for text in texts:

        text = text.lower()

        current_words = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            text
        )

        for word in current_words:

            if word not in stop_words:

                words.append(word)

    return Counter(
        words
    ).most_common(top_n)


top_words = get_top_words(
    filtered_df["text"]
)

if top_words:

    words_df = pd.DataFrame(
        top_words,
        columns=[
            "word",
            "count"
        ]
    )

    words_df = words_df.sort_values(
        "count"
    )

    fig_words = px.bar(
        words_df,
        x="count",
        y="word",
        orientation="h",
        text="count",
        title="Top 20 Most Common Words"
    )

    fig_words.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_words,
        use_container_width=True
    )

else:

    st.info(
        "Not enough text data."
    )


# ============================================================
# REVIEW TABLE
# ============================================================

st.subheader(
    "💬 Collected Reviews"
)

display_columns = [
    "business_name",
    "author_name",
    "rating",
    "review_date",
    "sentiment",
    "text"
]

display_columns = [
    column
    for column in display_columns
    if column in filtered_df.columns
]

st.dataframe(
    filtered_df[
        display_columns
    ],
    use_container_width=True,
    hide_index=True,
    height=500
)


# ============================================================
# DOWNLOAD
# ============================================================

st.subheader(
    "📥 Export"
)

csv_data = (
    filtered_df
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    "Download Filtered Reviews",
    data=csv_data,
    file_name="reviewlens_filtered_reviews.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "ReviewLens | Selenium + Pandas + Streamlit + Plotly"
)