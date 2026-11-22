from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import get_connection


def find_similar_reports(title, description, threshold=0.60):

    new_complaint = title + " " + description

    connection = get_connection()

    try:
        existing_reports = connection.execute(
            """
            SELECT id, title, description, category, status
            FROM reports
            ORDER BY id DESC
            """
        ).fetchall()

        if not existing_reports:
            return []

        complaint_texts = [
            new_complaint
        ]

        for report in existing_reports:
            complaint_texts.append(
                report["title"] + " " + report["description"]
            )

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        vectors = vectorizer.fit_transform(complaint_texts)

        similarities = cosine_similarity(
            vectors[0:1],
            vectors[1:]
        ).flatten()

        matches = []

        for index, score in enumerate(similarities):

            if score >= threshold:

                report = existing_reports[index]

                matches.append({
                    "report_id": report["id"],
                    "title": report["title"],
                    "category": report["category"],
                    "status": report["status"],
                    "similarity": round(float(score), 3)
                })

        matches.sort(
            key=lambda item: item["similarity"],
            reverse=True
        )

        return matches

    finally:
        connection.close()