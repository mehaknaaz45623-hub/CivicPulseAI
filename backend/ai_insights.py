from database import get_connection


def get_ai_insights():
    connection = get_connection()

    try:
        reports = connection.execute("""
            SELECT
                id,
                title,
                category,
                description,
                latitude,
                longitude,
                status,
                severity,
                created_at
            FROM reports
            ORDER BY created_at DESC
        """).fetchall()

        total = len(reports)

        category_counts = {}
        severity_counts = {
            "High": 0,
            "Medium": 0,
            "Low": 0
        }

        unresolved_high = []
        area_counts = {}

        for report in reports:
            category = report["category"]
            severity = report["severity"]
            status = report["status"]

            category_counts[category] = (
                category_counts.get(category, 0) + 1
            )

            if severity in severity_counts:
                severity_counts[severity] += 1

            if severity == "High" and status != "Resolved":
                unresolved_high.append({
                    "id": report["id"],
                    "title": report["title"],
                    "category": category,
                    "status": status
                })

            latitude = report["latitude"]
            longitude = report["longitude"]

            if latitude is not None and longitude is not None:
                area_key = (
                    round(latitude, 3),
                    round(longitude, 3)
                )

                area_counts[area_key] = (
                    area_counts.get(area_key, 0) + 1
                )

        recurring_categories = sorted(
            [
                {
                    "category": category,
                    "count": count
                }
                for category, count in category_counts.items()
                if count >= 2
            ],
            key=lambda item: item["count"],
            reverse=True
        )

        recurring_areas = sorted(
            [
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "complaint_count": count
                }
                for (latitude, longitude), count
                in area_counts.items()
                if count >= 2
            ],
            key=lambda item: item["complaint_count"],
            reverse=True
        )

        recommendations = []

        if unresolved_high:
            recommendations.append(
                "Review unresolved high-severity complaints first."
            )

        if recurring_categories:
            top_category = recurring_categories[0]["category"]
            recommendations.append(
                f"Investigate recurring {top_category} complaints."
            )

        if recurring_areas:
            recommendations.append(
                "Inspect locations with repeated complaint reports."
            )

        if not recommendations:
            recommendations.append(
                "Continue monitoring incoming civic complaints."
            )

        return {
            "total_complaints": total,
            "category_summary": category_counts,
            "severity_summary": severity_counts,
            "recurring_categories": recurring_categories,
            "recurring_areas": recurring_areas,
            "unresolved_high_priority": unresolved_high,
            "admin_recommendations": recommendations
        }

    finally:
        connection.close()