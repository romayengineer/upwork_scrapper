import sqlite3
import re
import config
from collections import Counter
from nltk.corpus import stopwords

STOP_WORDS = stopwords.words('english')


def get_all_text() -> str:
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, description FROM jobs")
    rows = cursor.fetchall()
    conn.close()

    texts = []
    for title, description in rows:
        if title:
            texts.append(title)
        if description:
            texts.append(description)

    return " ".join(texts)


def count_word_frequency(text: str) -> Counter:
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return Counter(filtered_words)


def print_word_frequency(counter: Counter, top: int):
    print(f"{'Word':<25} {'Count':>10}")
    print("-" * 35)
    for word, count in counter.most_common(top):
        print(f"{word:<25} {count:>10}")


def main():
    print("Reading jobs from database...")
    text = get_all_text()

    if not text:
        print("No jobs found in database.")
        return

    print(f"Total characters: {len(text)}")

    print("\nCounting word frequency...")
    word_counts = count_word_frequency(text)

    print(f"\nUnique words (after removing stop words): {len(word_counts)}")
    print("\n" + "=" * 35)
    print("WORD FREQUENCY (Most Common)")
    print("=" * 35 + "\n")

    print_word_frequency(word_counts, 100)


if __name__ == "__main__":
    main()
