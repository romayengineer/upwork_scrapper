import os
import sys
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
from dotenv import load_dotenv

DB_PATH = Path(__file__).parent / "jobs.db"


def get_jobs() -> list[tuple[str, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, description FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    return rows


def combine_text(title: str, description: str) -> str:
    parts = []
    if title:
        parts.append(title)
    if description:
        parts.append(description)
    return " ".join(parts)


def generate_embeddings(texts: list[str]) -> np.ndarray:
    print("Loading sentence transformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Generating embeddings (this may take a minute)...")
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings


def cluster_jobs(embeddings: np.ndarray, n_clusters: int) -> tuple:
    print(f"Clustering into {n_clusters} groups...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    return labels


def get_cluster_keywords(
    texts: list[str], labels: np.ndarray, n_keywords: int = 3
) -> dict:
    print("Extracting cluster keywords...")
    cluster_keywords = {}
    unique_labels = np.unique(labels)

    for cluster_id in unique_labels:
        cluster_texts = [texts[i] for i in range(len(texts)) if labels[i] == cluster_id]

        if not cluster_texts:
            cluster_keywords[cluster_id] = f"Cluster {cluster_id}"
            continue

        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=1000,
            ngram_range=(1, 1),
            min_df=1,
            max_df=0.95,
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(cluster_texts)
            feature_names = vectorizer.get_feature_names_out()
            mean_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
            top_indices = mean_tfidf.argsort()[-n_keywords:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            cluster_keywords[cluster_id] = " ".join(top_words).title()
        except ValueError:
            cluster_keywords[cluster_id] = f"Cluster {cluster_id}"

    return cluster_keywords


def update_categories(jobs: list[tuple], clusters: np.ndarray, keywords: dict):
    print("Updating database with categories...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    for i, job in enumerate(jobs):
        url, title, description = job
        cluster_id = clusters[i]
        category = keywords.get(cluster_id, f"Cluster {cluster_id}")

        cursor.execute("UPDATE jobs SET category = ? WHERE url = ?", (category, url))
        if cursor.rowcount > 0:
            count += 1

    conn.commit()
    conn.close()
    print(f"Updated {count} jobs with categories.")


def print_summary(jobs: list[tuple], clusters: np.ndarray, keywords: dict):
    print("\n" + "=" * 60)
    print("CLUSTER SUMMARY")
    print("=" * 60)

    unique_labels = np.unique(clusters)

    for cluster_id in sorted(unique_labels):
        cluster_indices = np.where(clusters == cluster_id)[0]
        category = keywords.get(cluster_id, f"Cluster {cluster_id}")

        print(f"\n{category} ({len(cluster_indices)} jobs)")
        print("-" * 40)

        for idx in cluster_indices[:3]:
            url, title, _ = jobs[idx]
            truncated_title = title[:60] + "..." if len(title) > 60 else title
            print(f"  • {truncated_title}")

        if len(cluster_indices) > 3:
            print(f"  ... and {len(cluster_indices) - 3} more")


def main(n_clusters: int):
    print(f"Starting job clustering with {n_clusters} clusters...\n")

    jobs = get_jobs()
    if not jobs:
        print("No jobs found in database.")
        return

    print(f"Found {len(jobs)} jobs in database.")

    texts = [combine_text(title, desc) for url, title, desc in jobs]

    embeddings = generate_embeddings(texts)
    clusters = cluster_jobs(embeddings, n_clusters)
    keywords = get_cluster_keywords(texts, clusters)

    update_categories(jobs, clusters, keywords)
    print_summary(jobs, clusters, keywords)


if __name__ == "__main__":
    load_dotenv()

    n_clusters = int(os.getenv("CLUSTER_COUNT"))
    if len(sys.argv) > 1:
        try:
            n_clusters = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number: {sys.argv[1]}, using default 8")

    main(n_clusters)
