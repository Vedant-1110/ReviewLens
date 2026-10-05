import os
import re
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/scraped_reviews.csv"

OUTPUT_DIR = "output"
CHART_DIR = "output/charts"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)


# ============================================================
# SENTIMENT
# ============================================================

def rating_sentiment(rating):

    if rating >= 4:
        return "Positive"

    elif rating == 3:
        return "Neutral"

    else:
        return "Negative"


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-zA-Z\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TOP WORDS
# ============================================================

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
        "had",
        "been",
        "were",
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

        cleaned = clean_text(text)

        current_words = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            cleaned
        )

        for word in current_words:

            if word not in stop_words:

                words.append(word)

    return Counter(words).most_common(
        top_n
    )


# ============================================================
# MAIN ANALYSIS
# ============================================================

def run_analysis():

    print("\n")
    print("=" * 60)
    print("              REVIEWLENS ANALYSIS")
    print("=" * 60)

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"File not found: {INPUT_FILE}"
        )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"\nLoaded {len(df)} reviews."
    )

    # --------------------------------------------------------
    # BASIC CLEANING
    # --------------------------------------------------------

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

    df["text"] = (
        df["text"]
        .fillna("")
        .astype(str)
    )

    df["business_name"] = (
        df["business_name"]
        .fillna("Unknown")
        .astype(str)
    )

    df["author_name"] = (
        df["author_name"]
        .fillna("Unknown")
        .astype(str)
    )

    df["review_date"] = (
        df["review_date"]
        .fillna("")
        .astype(str)
    )

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    df["sentiment"] = (
        df["rating"]
        .apply(rating_sentiment)
    )

    # --------------------------------------------------------
    # TEXT METRICS
    # --------------------------------------------------------

    df["cleaned_text"] = (
        df["text"]
        .apply(clean_text)
    )

    df["review_length"] = (
        df["text"]
        .str.len()
    )

    df["word_count"] = (
        df["text"]
        .str.split()
        .str.len()
    )

    # --------------------------------------------------------
    # SAVE ANALYZED DATA
    # --------------------------------------------------------

    df.to_csv(
        f"{OUTPUT_DIR}/analyzed_reviews.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # BUSINESS SUMMARY
    # --------------------------------------------------------

    business_summary = (
        df.groupby("business_name")
        .agg(
            total_reviews=("rating", "count"),
            average_rating=("rating", "mean"),
            average_review_length=(
                "review_length",
                "mean"
            ),
            average_word_count=(
                "word_count",
                "mean"
            )
        )
        .reset_index()
    )

    business_summary[
        "average_rating"
    ] = business_summary[
        "average_rating"
    ].round(2)

    business_summary.to_csv(
        f"{OUTPUT_DIR}/business_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # CATEGORY SUMMARY
    # --------------------------------------------------------

    if "rating_category" in df.columns:

        category_summary = (
            df.groupby("rating_category")
            .agg(
                reviews=("rating", "count"),
                average_rating=("rating", "mean")
            )
            .reset_index()
        )

        category_summary[
            "average_rating"
        ] = category_summary[
            "average_rating"
        ].round(2)

    else:

        category_summary = pd.DataFrame(
            columns=[
                "rating_category",
                "reviews",
                "average_rating"
            ]
        )

    category_summary.to_csv(
        f"{OUTPUT_DIR}/category_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # TOP WORDS
    # --------------------------------------------------------

    top_words = get_top_words(
        df["text"]
    )

    top_words_df = pd.DataFrame(
        top_words,
        columns=[
            "word",
            "count"
        ]
    )

    top_words_df.to_csv(
        f"{OUTPUT_DIR}/top_words.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # PRINT SUMMARY
    # --------------------------------------------------------

    print("\nANALYSIS SUMMARY")
    print("-" * 40)

    print(
        f"Total reviews: {len(df)}"
    )

    print(
        f"Average rating: "
        f"{df['rating'].mean():.2f}"
    )

    print(
        f"Positive: "
        f"{len(df[df['sentiment'] == 'Positive'])}"
    )

    print(
        f"Neutral: "
        f"{len(df[df['sentiment'] == 'Neutral'])}"
    )

    print(
        f"Negative: "
        f"{len(df[df['sentiment'] == 'Negative'])}"
    )

    # --------------------------------------------------------
    # CHART 1 - RATING DISTRIBUTION
    # --------------------------------------------------------

    rating_counts = (
        df["rating"]
        .value_counts()
        .sort_index()
    )

    plt.figure(
        figsize=(8, 5)
    )

    rating_counts.plot(
        kind="bar"
    )

    plt.title(
        "Restaurant Rating Distribution"
    )

    plt.xlabel(
        "Rating"
    )

    plt.ylabel(
        "Number of Reviews"
    )

    plt.tight_layout()

    plt.savefig(
        f"{CHART_DIR}/rating_distribution.png"
    )

    plt.close()

    # --------------------------------------------------------
    # CHART 2 - SENTIMENT DISTRIBUTION
    # --------------------------------------------------------

    sentiment_counts = (
        df["sentiment"]
        .value_counts()
    )

    plt.figure(
        figsize=(8, 5)
    )

    sentiment_counts.plot(
        kind="bar"
    )

    plt.title(
        "Review Sentiment Distribution"
    )

    plt.xlabel(
        "Sentiment"
    )

    plt.ylabel(
        "Number of Reviews"
    )

    plt.tight_layout()

    plt.savefig(
        f"{CHART_DIR}/sentiment_distribution.png"
    )

    plt.close()

    # --------------------------------------------------------
    # CHART 3 - REVIEW LENGTH BY RATING
    # --------------------------------------------------------

    plt.figure(
        figsize=(8, 5)
    )

    df.boxplot(
        column="review_length",
        by="rating"
    )

    plt.title(
        "Review Length by Rating"
    )

    plt.suptitle("")

    plt.xlabel(
        "Rating"
    )

    plt.ylabel(
        "Characters"
    )

    plt.tight_layout()

    plt.savefig(
        f"{CHART_DIR}/review_length_by_rating.png"
    )

    plt.close()

    # --------------------------------------------------------
    # CHART 4 - TOP WORDS
    # --------------------------------------------------------

    if not top_words_df.empty:

        top_words_df = (
            top_words_df
            .sort_values(
                "count",
                ascending=True
            )
        )

        plt.figure(
            figsize=(9, 6)
        )

        plt.barh(
            top_words_df["word"],
            top_words_df["count"]
        )

        plt.title(
            "Most Common Words"
        )

        plt.xlabel(
            "Frequency"
        )

        plt.ylabel(
            "Word"
        )

        plt.tight_layout()

        plt.savefig(
            f"{CHART_DIR}/top_words.png"
        )

        plt.close()

    print(
        "\n✅ Analysis completed."
    )

    print(
        "Output files saved in:",
        OUTPUT_DIR
    )

    return df


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    run_analysis()