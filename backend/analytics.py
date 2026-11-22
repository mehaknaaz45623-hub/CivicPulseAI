from database import get_connection


def get_dashboard_analytics():

    connection = get_connection()

    try:
        # Total complaints
        total = connection.execute(
            "SELECT COUNT(*) FROM reports"
        ).fetchone()[0]

        # Complaints by status
        status_rows = connection.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM reports
            GROUP BY status
            """
        ).fetchall()

        status_counts = {
            "Pending": 0,
            "In Progress": 0,
            "Resolved": 0
        }

        for row in status_rows:
            status_counts[row["status"]] = row["count"]

        # Complaints by category
        category_rows = connection.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM reports
            GROUP BY category
            ORDER BY count DESC
            """
        ).fetchall()

        category_counts = {
            row["category"]: row["count"]
            for row in category_rows
        }

        # Complaints by severity
        severity_rows = connection.execute(
            """
            SELECT severity, COUNT(*) AS count
            FROM reports
            GROUP BY severity
            """
        ).fetchall()

        severity_counts = {
            "High": 0,
            "Medium": 0,
            "Low": 0
        }

        for row in severity_rows:
            severity_counts[row["severity"]] = row["count"]

        return {
            "total_complaints": total,
            "status_summary": status_counts,
            "category_summary": category_counts,
            "severity_summary": severity_counts
        }

    finally:
        connection.close()


# ---------------- HISTORICAL TREND ANALYSIS ----------------

def get_historical_trends():

    connection = get_connection()

    try:

        # Daily complaint trends
        daily_rows = connection.execute(
            """
            SELECT
                DATE(created_at) AS report_date,
                COUNT(*) AS complaint_count
            FROM reports
            GROUP BY DATE(created_at)
            ORDER BY report_date ASC
            """
        ).fetchall()

        daily_trends = [
            {
                "date": row["report_date"],
                "complaints": row["complaint_count"]
            }
            for row in daily_rows
        ]

        # Monthly complaint trends
        monthly_rows = connection.execute(
            """
            SELECT
                STRFTIME('%Y-%m', created_at) AS report_month,
                COUNT(*) AS complaint_count
            FROM reports
            GROUP BY STRFTIME('%Y-%m', created_at)
            ORDER BY report_month ASC
            """
        ).fetchall()

        monthly_trends = [
            {
                "month": row["report_month"],
                "complaints": row["complaint_count"]
            }
            for row in monthly_rows
        ]

        # Most frequently reported categories
        category_rows = connection.execute(
            """
            SELECT
                category,
                COUNT(*) AS complaint_count
            FROM reports
            GROUP BY category
            ORDER BY complaint_count DESC
            """
        ).fetchall()

        category_trends = [
            {
                "category": row["category"],
                "complaints": row["complaint_count"]
            }
            for row in category_rows
        ]

        # Overall historical statistics
        total = connection.execute(
            "SELECT COUNT(*) FROM reports"
        ).fetchone()[0]

        active = connection.execute(
            """
            SELECT COUNT(*)
            FROM reports
            WHERE status != 'Resolved'
            """
        ).fetchone()[0]

        resolved = connection.execute(
            """
            SELECT COUNT(*)
            FROM reports
            WHERE status = 'Resolved'
            """
        ).fetchone()[0]

        return {
            "total_complaints": total,
            "active_complaints": active,
            "resolved_complaints": resolved,
            "daily_trends": daily_trends,
            "monthly_trends": monthly_trends,
            "category_trends": category_trends
        }

    finally:
        connection.close()