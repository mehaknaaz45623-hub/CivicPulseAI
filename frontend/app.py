import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import requests
import plotly.express as px
import pandas as pd
import folium
from streamlit_folium import st_folium


API_URL = "http://127.0.0.1:8000"


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="CivicPulse AI",
    page_icon="🏙️",
    layout="wide"
)


# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #07111f, #0b1930, #101d35);
    color: #eaf6ff;
}
section[data-testid="stSidebar"] {
    background: #081525;
    border-right: 1px solid #163b59;
}
h1, h2, h3 {
    color: #55dcff !important;
}
p, label, span {
    color: #d5e8f5;
}
div.stButton > button {
    background: linear-gradient(90deg, #087fca, #00c9d8);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: bold;
}
div.stButton > button:hover {
    background: linear-gradient(90deg, #00a4ed, #00e5ee);
    color: white;
}
div[data-testid="stMetric"] {
    background: #102640;
    border: 1px solid #17618a;
    padding: 18px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None

if "selected_latitude" not in st.session_state:
    st.session_state.selected_latitude = None

if "selected_longitude" not in st.session_state:
    st.session_state.selected_longitude = None


# ---------------- API HELPERS ----------------

def get_headers():
    return {
        "Authorization": f"Bearer {st.session_state.token}"
    }


def show_api_error(error):
    try:
        detail = error.response.json().get(
            "detail", "Something went wrong."
        )
    except Exception:
        detail = "Could not connect to the backend."

    st.error(str(detail))


def get_reports():
    response = requests.get(
        f"{API_URL}/reports",
        headers=get_headers(),
        timeout=30
    )
    response.raise_for_status()

    reports = response.json()

    if isinstance(reports, dict):
        reports = reports.get("reports", [])

    return reports if isinstance(reports, list) else []


def get_admin_data(endpoint):
    response = requests.get(
        f"{API_URL}{endpoint}",
        headers=get_headers(),
        timeout=60
    )
    response.raise_for_status()
    return response.json()


def to_chart_rows(value, name_key="name", value_key="count"):
    """Convert common API dictionary/list formats into chart rows."""
    rows = []

    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (int, float)):
                rows.append({
                    name_key: str(key),
                    value_key: item
                })
            elif isinstance(item, dict):
                label = (
                    item.get(name_key)
                    or item.get("category")
                    or item.get("date")
                    or item.get("month")
                    or str(key)
                )
                number = (
                    item.get(value_key)
                    or item.get("count")
                    or item.get("total")
                    or item.get("value")
                    or 0
                )
                rows.append({
                    name_key: str(label),
                    value_key: number
                })

    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, dict):
                label = (
                    item.get(name_key)
                    or item.get("category")
                    or item.get("date")
                    or item.get("month")
                    or item.get("area")
                    or f"Item {index + 1}"
                )
                number = (
                    item.get(value_key)
                    or item.get("count")
                    or item.get("total")
                    or item.get("value")
                    or 0
                )
                rows.append({
                    name_key: str(label),
                    value_key: number
                })
            elif isinstance(item, (int, float)):
                rows.append({
                    name_key: f"Item {index + 1}",
                    value_key: item
                })

    return rows


def show_admin_table_or_message(data, empty_message):
    if isinstance(data, list) and data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    elif isinstance(data, dict) and data:
        st.dataframe(
            pd.DataFrame(
                [{"Name": key, "Value": value} for key, value in data.items()]
            ),
            use_container_width=True
        )
    else:
        st.info(empty_message)


# ---------------- HEADER ----------------

st.markdown(
    "<h1 style='text-align:center;'>🏙️ CivicPulse AI</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;color:#55dcff;'>"
    "INTELLIGENT SMART CITY COMPLAINT MANAGEMENT"
    "</p>",
    unsafe_allow_html=True
)

st.divider()


# ---------------- AUTHENTICATION ----------------

if not st.session_state.token:

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Register"]
    )

    with login_tab:
        st.subheader("Welcome Back")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if login_button:
            try:
                response = requests.post(
                    f"{API_URL}/auth/login",
                    data={
                        "username": email,
                        "password": password
                    },
                    timeout=30
                )
                response.raise_for_status()

                result = response.json()
                st.session_state.token = result["access_token"]

                profile_response = requests.get(
                    f"{API_URL}/auth/me",
                    headers=get_headers(),
                    timeout=30
                )
                profile_response.raise_for_status()

                st.session_state.user = profile_response.json()
                st.success("Login successful!")
                st.rerun()

            except requests.RequestException as error:
                show_api_error(error)
            except (KeyError, TypeError, ValueError):
                st.error("Unexpected login response from backend.")

    with register_tab:
        st.subheader("Create Your Account")

        with st.form("register_form"):
            name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_password = st.text_input(
                "Create Password",
                type="password"
            )
            register_button = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

        if register_button:
            if not name.strip() or not new_email.strip() or not new_password:
                st.warning("Please complete all registration fields.")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/register",
                        json={
                            "name": name,
                            "email": new_email,
                            "password": new_password
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    st.success("Account created! You can now log in.")
                except requests.RequestException as error:
                    show_api_error(error)


# ---------------- LOGGED-IN APPLICATION ----------------

else:

    user = st.session_state.user or {}
    role = user.get("role", "citizen")

    # ---------------- SIDEBAR ----------------

    with st.sidebar:
        st.title("CIVICPULSE")
        st.caption("SMART CITY CONTROL CENTER")
        st.write(f"Welcome, **{user.get('name', 'User')}**")
        st.write(f"Role: **{role.title()}**")

        if role == "admin":
            pages = [
                "Dashboard",
                "Admin Analytics",
                "3D Smart City",
                "Live Complaint Map",
                "All Complaints",
                "AI Analysis",
                "AI Insights",
                "Historical Trends"
            ]
        else:
            pages = [
                "Dashboard",
                "3D Smart City",
                "Submit Complaint",
                "My Complaints",
                "AI Analysis"
            ]

        selected_page = st.radio("Navigation", pages)
        st.divider()

        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()


    # ---------------- DASHBOARD ----------------

    if selected_page == "Dashboard":

        st.title("🌐 Smart City Dashboard")

        try:
            reports = get_reports()
            total = len(reports)

            pending = sum(r.get("status") == "Pending" for r in reports)
            progress = sum(r.get("status") == "In Progress" for r in reports)
            resolved = sum(r.get("status") == "Resolved" for r in reports)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Reports", total)
            col2.metric("Pending", pending)
            col3.metric("In Progress", progress)
            col4.metric("Resolved", resolved)

            st.subheader("📊 Complaint Overview")

            if reports:
                chart_data = {
                    "Status": ["Pending", "In Progress", "Resolved"],
                    "Count": [pending, progress, resolved]
                }

                fig = px.bar(
                    chart_data,
                    x="Status",
                    y="Count",
                    color="Status",
                    title="Complaints by Status",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No complaints available yet.")

        except requests.RequestException as error:
            show_api_error(error)



    # ---------------- ADMIN ANALYTICS ----------------

    elif selected_page == "Admin Analytics":

        st.title("📊 Admin Analytics")
        st.write(
            "Monitor complaint volume, resolution progress, categories, "
            "severity levels, and recent civic reports."
        )

        if role != "admin":
            st.error("Administrator access is required to view Admin Analytics.")
        else:
            try:
                reports = get_reports()

                if not reports:
                    st.info(
                        "No complaint data is available yet. "
                        "Analytics will appear after citizens submit complaints."
                    )
                else:
                    reports_df = pd.DataFrame(reports)

                    for column, default in (
                        ("status", "Pending"),
                        ("category", "Unknown"),
                        ("severity", "Unknown"),
                        ("title", "Untitled"),
                    ):
                        if column not in reports_df.columns:
                            reports_df[column] = default
                        reports_df[column] = (
                            reports_df[column]
                            .fillna(default)
                            .astype(str)
                        )

                    total = len(reports_df)
                    status_values = reports_df["status"].str.strip().str.lower()
                    pending_count = int(status_values.eq("pending").sum())
                    progress_count = int(
                        status_values.isin(["in progress", "in_progress"]).sum()
                    )
                    resolved_count = int(status_values.eq("resolved").sum())
                    other_count = total - pending_count - progress_count - resolved_count
                    resolution_rate = (
                        (resolved_count / total) * 100 if total else 0
                    )

                    st.subheader("📌 Overall Performance")
                    metric_columns = st.columns(5)
                    metric_columns[0].metric("Total Complaints", total)
                    metric_columns[1].metric("Pending", pending_count)
                    metric_columns[2].metric("In Progress", progress_count)
                    metric_columns[3].metric("Resolved", resolved_count)
                    metric_columns[4].metric(
                        "Resolution Rate", f"{resolution_rate:.1f}%"
                    )

                    if other_count:
                        st.caption(
                            f"{other_count} complaint(s) have another or "
                            "unrecognised status and are included in the total."
                        )

                    st.divider()
                    left_chart, right_chart = st.columns(2)

                    with left_chart:
                        st.subheader("📍 Complaints by Category")
                        category_counts = (
                            reports_df["category"]
                            .value_counts()
                            .rename_axis("Category")
                            .reset_index(name="Complaints")
                        )
                        category_fig = px.bar(
                            category_counts,
                            x="Category",
                            y="Complaints",
                            color="Category",
                            template="plotly_dark",
                            title="Category Distribution",
                        )
                        st.plotly_chart(
                            category_fig, use_container_width=True
                        )

                    with right_chart:
                        st.subheader("⚠️ Complaints by Severity")
                        severity_counts = (
                            reports_df["severity"]
                            .value_counts()
                            .rename_axis("Severity")
                            .reset_index(name="Complaints")
                        )
                        severity_fig = px.pie(
                            severity_counts,
                            names="Severity",
                            values="Complaints",
                            hole=0.42,
                            template="plotly_dark",
                            title="Severity Distribution",
                        )
                        st.plotly_chart(
                            severity_fig, use_container_width=True
                        )

                    st.divider()
                    st.subheader("🔄 Complaint Status Breakdown")
                    status_counts = (
                        reports_df["status"]
                        .value_counts()
                        .rename_axis("Status")
                        .reset_index(name="Complaints")
                    )
                    status_fig = px.bar(
                        status_counts,
                        x="Status",
                        y="Complaints",
                        color="Status",
                        template="plotly_dark",
                        title="Current Complaint Status",
                    )
                    st.plotly_chart(status_fig, use_container_width=True)

                    st.divider()
                    st.subheader("🕒 Recent Complaints")
                    recent_df = reports_df.copy()
                    if "created_at" in recent_df.columns:
                        recent_df["_sort_date"] = pd.to_datetime(
                            recent_df["created_at"], errors="coerce", utc=True
                        )
                        recent_df = recent_df.sort_values(
                            "_sort_date", ascending=False, na_position="last"
                        )

                    display_columns = [
                        column for column in (
                            "id", "title", "category", "severity",
                            "status", "created_at"
                        )
                        if column in recent_df.columns
                    ]
                    st.dataframe(
                        recent_df[display_columns].head(10),
                        use_container_width=True,
                        hide_index=True,
                    )

                    with st.expander("View complete analytics data"):
                        st.dataframe(
                            reports_df,
                            use_container_width=True,
                            hide_index=True,
                        )

                if st.button("🔄 Refresh Admin Analytics"):
                    st.rerun()

            except requests.RequestException as error:
                show_api_error(error)
            except (ValueError, TypeError, KeyError) as error:
                st.error(f"Could not display Admin Analytics: {error}")


    # ---------------- 3D SMART CITY ----------------

    elif selected_page == "3D Smart City":

        st.title("🏙️ Interactive 3D Smart City")
        st.write(
            "Explore the CivicPulse AI smart city environment. "
            "Drag to rotate and scroll to zoom."
        )

        city_file = Path(__file__).with_name("smart_city.html")

        if city_file.exists():
            city_html = city_file.read_text(encoding="utf-8")
            components.html(
                city_html,
                height=670,
                scrolling=False
            )
        else:
            st.error(
                "smart_city.html was not found in the frontend folder."
            )


    # ---------------- ADMIN LIVE COMPLAINT MAP ----------------

    elif selected_page == "Live Complaint Map":

        st.title("🗺️ Admin Live Complaint Map")
        st.write(
            "View reported civic issues across their submitted locations."
        )

        try:
            reports = get_reports()
            location_reports = []

            for report in reports:
                latitude = report.get("latitude")
                longitude = report.get("longitude")

                if latitude is None or longitude is None:
                    continue

                try:
                    latitude = float(latitude)
                    longitude = float(longitude)

                    if not (-90 <= latitude <= 90):
                        continue
                    if not (-180 <= longitude <= 180):
                        continue

                    location_reports.append(
                        (report, latitude, longitude)
                    )
                except (ValueError, TypeError):
                    continue

            total_locations = len(location_reports)

            pending_locations = sum(
                report.get("status") == "Pending"
                for report, _, _ in location_reports
            )
            progress_locations = sum(
                report.get("status") == "In Progress"
                for report, _, _ in location_reports
            )
            resolved_locations = sum(
                report.get("status") == "Resolved"
                for report, _, _ in location_reports
            )

            st.subheader("📊 Location Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Mapped Reports", total_locations)
            col2.metric("Pending", pending_locations)
            col3.metric("In Progress", progress_locations)
            col4.metric("Resolved", resolved_locations)

            st.divider()
            st.subheader("📍 Complaint Locations")
            st.markdown(
                "🔴 Pending &nbsp;&nbsp; 🟠 In Progress &nbsp;&nbsp; 🟢 Resolved",
                unsafe_allow_html=True
            )

            if location_reports:
                average_latitude = sum(
                    latitude for _, latitude, _ in location_reports
                ) / total_locations
                average_longitude = sum(
                    longitude for _, _, longitude in location_reports
                ) / total_locations

                complaint_map = folium.Map(
                    location=[average_latitude, average_longitude],
                    zoom_start=6,
                    control_scale=True
                )

                for report, latitude, longitude in location_reports:
                    status = report.get("status", "Pending")

                    if status == "Resolved":
                        marker_color = "green"
                    elif status == "In Progress":
                        marker_color = "orange"
                    else:
                        marker_color = "red"

                    title = html.escape(str(report.get("title", "Untitled")))
                    category = html.escape(str(report.get("category", "Unknown")))
                    description = html.escape(str(report.get("description", "")))
                    severity = html.escape(str(report.get("severity", "Unknown")))
                    safe_status = html.escape(str(status))
                    complaint_id = html.escape(str(report.get("id", "Unknown")))

                    popup_html = f"""
                    <div style="width:230px;">
                        <h4>Complaint #{complaint_id}</h4>
                        <b>Title:</b> {title}<br>
                        <b>Category:</b> {category}<br>
                        <b>Status:</b> {safe_status}<br>
                        <b>Severity:</b> {severity}<br>
                        <b>Description:</b><br>
                        {description}
                    </div>
                    """

                    folium.Marker(
                        location=[latitude, longitude],
                        tooltip=f"Complaint #{complaint_id}: {title}",
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(
                            color=marker_color,
                            icon="info-sign"
                        )
                    ).add_to(complaint_map)

                st_folium(
                    complaint_map,
                    height=620,
                    width=None,
                    key="admin_live_complaint_map"
                )

                st.success(
                    f"{total_locations} complaint location(s) displayed."
                )
            else:
                st.info(
                    "No complaints with valid map coordinates were found yet."
                )
                st.write(
                    "When citizens submit complaints with locations, "
                    "their markers will appear here."
                )

            if len(reports) > total_locations:
                st.warning(
                    f"{len(reports) - total_locations} complaint(s) "
                    "do not have valid coordinates and cannot be mapped."
                )

            if st.button("🔄 Refresh Complaint Map"):
                st.rerun()

        except requests.RequestException as error:
            show_api_error(error)


    # ---------------- SUBMIT COMPLAINT ----------------

    elif selected_page == "Submit Complaint":

        st.title("📝 Submit a Civic Complaint")
        st.write("Report an issue in your area.")

        with st.form("complaint_form"):
            title = st.text_input(
                "Complaint Title",
                placeholder="Example: Garbage not collected"
            )
            description = st.text_area(
                "Describe the Issue",
                placeholder="Explain the civic issue in detail..."
            )

            st.subheader("📍 Location Details")
            latitude = st.number_input(
                "Latitude",
                value=12.9716,
                format="%.6f"
            )
            longitude = st.number_input(
                "Longitude",
                value=77.5946,
                format="%.6f"
            )

            submitted = st.form_submit_button(
                "🚀 Submit Complaint",
                use_container_width=True
            )

            if submitted:
                if not title.strip() or not description.strip():
                    st.warning("Please enter both title and description.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/reports",
                            headers=get_headers(),
                            json={
                                "title": title,
                                "description": description,
                                "latitude": latitude,
                                "longitude": longitude
                            },
                            timeout=60
                        )
                        response.raise_for_status()
                        st.success("Complaint submitted successfully!")
                        st.json(response.json())
                    except requests.RequestException as error:
                        show_api_error(error)


    # ---------------- MY / ALL COMPLAINTS ----------------

    elif selected_page in ["My Complaints", "All Complaints"]:

        if selected_page == "My Complaints":
            st.title("📋 My Complaints")
            st.write("Track the complaints you have submitted.")
        else:
            st.title("📋 All Citizen Complaints")
            st.write("View complaints submitted by citizens.")

        try:
            reports = get_reports()

            if not reports:
                st.info("No complaints found.")
            else:
                for report in reports:
                    with st.expander(
                        f"#{report.get('id')} — "
                        f"{report.get('title', 'Untitled')}"
                    ):
                        st.write(
                            "**Category:**",
                            report.get("category", "Not available")
                        )
                        st.write(
                            "**Description:**",
                            report.get("description", "Not available")
                        )
                        st.write(
                            "**Severity:**",
                            report.get("severity", "Not available")
                        )
                        st.write(
                            "**Status:**",
                            report.get("status", "Pending")
                        )
                        st.write("**Latitude:**", report.get("latitude"))
                        st.write("**Longitude:**", report.get("longitude"))
                        st.write(
                            "**Created At:**",
                            report.get("created_at", "Not available")
                        )

                        if report.get("ai_confidence") is not None:
                            st.write(
                                "**AI Confidence:**",
                                report.get("ai_confidence")
                            )

                        # Admin-only complaint status management.
                        if selected_page == "All Complaints" and role == "admin":
                            st.divider()
                            st.subheader("🛠️ Manage Complaint Status")

                            allowed_statuses = [
                                "Pending",
                                "In Progress",
                                "Resolved"
                            ]

                            current_status = report.get("status", "Pending")
                            if current_status not in allowed_statuses:
                                current_status = "Pending"

                            report_id = report.get("id")

                            selected_status = st.selectbox(
                                "Update Status",
                                allowed_statuses,
                                index=allowed_statuses.index(current_status),
                                key=f"status_select_{report_id}"
                            )

                            if st.button(
                                "💾 Save Status",
                                key=f"save_status_{report_id}",
                                use_container_width=True
                            ):
                                try:
                                    status_response = requests.patch(
                                        f"{API_URL}/reports/{report_id}/status",
                                        headers=get_headers(),
                                        json={"status": selected_status},
                                        timeout=30
                                    )
                                    status_response.raise_for_status()

                                    st.success(
                                        f"Complaint #{report_id} status updated "
                                        f"to {selected_status}."
                                    )
                                    st.rerun()

                                except requests.RequestException as error:
                                    show_api_error(error)

        except requests.RequestException as error:
            show_api_error(error)


    # ---------------- AI ANALYSIS ----------------

    elif selected_page == "AI Analysis":

        st.title("🤖 CivicPulse AI Analysis")
        st.write(
            "Use AI-powered tools to analyse civic complaints "
            "and uploaded images."
        )

        st.markdown("---")
        st.subheader("🧠 Text Complaint Classification")

        complaint_text = st.text_area(
            "Enter a complaint description",
            placeholder=(
                "Example: Garbage has not been collected "
                "for several days..."
            )
        )

        if st.button("Analyse Complaint", use_container_width=True):
            if not complaint_text.strip():
                st.warning("Please enter a complaint description.")
            else:
                try:
                    complaint_title = (
                        complaint_text.strip().splitlines()[0][:80]
                    )

                    response = requests.post(
                        f"{API_URL}/ai/classify",
                        headers=get_headers(),
                        json={
                            "title": complaint_title,
                            "description": complaint_text.strip()
                        },
                        timeout=60
                    )
                    response.raise_for_status()
                    result = response.json()

                    st.success("AI analysis completed!")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Category", result.get("category", "Unknown"))
                    col2.metric("Severity", result.get("severity", "Unknown"))
                    col3.metric("Priority Score", result.get("priority_score", 0))

                    st.write("**Explanation:**")
                    st.write(
                        result.get(
                            "explanation",
                            "No explanation available."
                        )
                    )
                    st.write("**Risk Indicators:**")
                    st.write(result.get("risk_indicators", []))
                    st.caption(
                        "AI predictions are estimates and should "
                        "be reviewed by a human."
                    )

                except requests.RequestException as error:
                    show_api_error(error)

        st.markdown("---")
        st.subheader("🔎 Duplicate Complaint Detection")
        st.write(
            "Check whether a complaint is similar to an existing report. "
            "Matches are suggestions for review, not confirmed duplicates."
        )

        duplicate_title = st.text_input(
            "Complaint title for duplicate check",
            placeholder="Example: Garbage overflowing near public park",
            key="duplicate_check_title"
        )
        duplicate_description = st.text_area(
            "Complaint description for duplicate check",
            placeholder=(
                "Describe the civic issue and its location..."
            ),
            key="duplicate_check_description"
        )

        if st.button(
            "🔍 Check Similar Complaints",
            use_container_width=True,
            key="run_duplicate_check"
        ):
            if not duplicate_title.strip() or not duplicate_description.strip():
                st.warning("Please enter both a title and description.")
            else:
                try:
                    duplicate_response = requests.post(
                        f"{API_URL}/ai/check-duplicates",
                        headers=get_headers(),
                        json={
                            "title": duplicate_title.strip(),
                            "description": duplicate_description.strip()
                        },
                        timeout=60
                    )
                    duplicate_response.raise_for_status()
                    duplicate_result = duplicate_response.json()
                    possible_duplicates = duplicate_result.get(
                        "possible_duplicates", []
                    )
                    matches_found = duplicate_result.get(
                        "matches_found", len(possible_duplicates)
                    )

                    if matches_found:
                        st.warning(
                            f"Found {matches_found} possible similar "
                            "complaint(s). Please review them."
                        )
                        for match in possible_duplicates:
                            similarity = match.get("similarity", 0)
                            with st.expander(
                                f"#{match.get('report_id', 'N/A')} — "
                                f"{match.get('title', 'Untitled')} "
                                f"({similarity:.1%} similarity)"
                            ):
                                st.write(
                                    "**Category:**",
                                    match.get("category", "Not available")
                                )
                                st.write(
                                    "**Current status:**",
                                    match.get("status", "Not available")
                                )
                                st.progress(
                                    max(0.0, min(float(similarity), 1.0))
                                )
                                st.caption(
                                    "Similarity is a text-based estimate; "
                                    "an administrator should verify the match."
                                )
                    else:
                        st.success(
                            "No similar complaints were found above the "
                            "current similarity threshold."
                        )

                except requests.RequestException as error:
                    show_api_error(error)
                except (ValueError, TypeError, AttributeError) as error:
                    st.error(
                        f"Could not display duplicate-check results: {error}"
                    )

        st.markdown("---")
        st.subheader("🖼️ AI Image Analysis")

        uploaded_image = st.file_uploader(
            "Upload an image of a civic issue",
            type=["jpg", "jpeg", "png", "webp"]
        )

        if uploaded_image is not None:
            st.image(
                uploaded_image,
                caption="Uploaded Civic Issue Image",
                use_container_width=True
            )

            if st.button("Analyse Image", use_container_width=True):
                try:
                    uploaded_image.seek(0)
                    files = {
                        "image": (
                            uploaded_image.name,
                            uploaded_image.getvalue(),
                            uploaded_image.type
                        )
                    }

                    response = requests.post(
                        f"{API_URL}/ai/analyze-image",
                        headers=get_headers(),
                        files=files,
                        timeout=120
                    )
                    response.raise_for_status()

                    result = response.json()
                    analysis = result.get("analysis", result)

                    st.success("Image analysis completed!")

                    confidence = float(analysis.get("confidence", 0))
                    if confidence <= 1:
                        confidence_display = f"{confidence:.2%}"
                    else:
                        confidence_display = f"{confidence:.2f}%"

                    col1, col2 = st.columns(2)
                    col1.metric(
                        "Predicted Issue",
                        analysis.get("predicted_issue", "Unknown")
                    )
                    col2.metric(
                        "Model Confidence",
                        confidence_display
                    )

                    st.write("**Other Predictions:**")
                    predictions = analysis.get("all_predictions", {})

                    if isinstance(predictions, dict) and predictions:
                        prediction_data = [
                            {
                                "Issue": issue,
                                "Confidence": (
                                    f"{float(score):.2f}%"
                                )
                            }
                            for issue, score in predictions.items()
                        ]
                        st.dataframe(
                            prediction_data,
                            use_container_width=True
                        )
                    elif predictions:
                        st.dataframe(
                            predictions,
                            use_container_width=True
                        )
                    else:
                        st.info("No additional predictions were returned.")

                    st.caption(
                        "Image predictions are experimental estimates, "
                        "not confirmed diagnoses of the issue."
                    )

                except requests.RequestException as error:
                    show_api_error(error)
                except (ValueError, TypeError, KeyError) as error:
                    st.error(
                        f"Could not display image analysis: {error}"
                    )


    # ---------------- AI INSIGHTS (ADMIN) ----------------

    elif selected_page == "AI Insights":

        st.title("🧠 CivicPulse AI Insights")
        st.write(
            "AI-supported summaries of complaint patterns, "
            "recurring civic issues, and areas that may need attention."
        )

        if role != "admin":
            st.error("Administrator access is required to view AI Insights.")
        else:
            try:
                data = get_admin_data("/admin/ai-insights")

                st.success("AI Insights loaded successfully.")

                total_complaints = data.get("total_complaints", 0)
                col1, col2 = st.columns(2)
                col1.metric("Total Complaints Analysed", total_complaints)

                high_priority = data.get(
                    "unresolved_high_priority", []
                )
                high_priority_count = (
                    len(high_priority)
                    if isinstance(high_priority, list)
                    else int(high_priority or 0)
                )
                col2.metric(
                    "Unresolved High-Priority Issues",
                    high_priority_count
                )

                st.divider()
                st.subheader("📊 Complaint Categories")

                category_summary = data.get("category_summary", {})
                category_rows = to_chart_rows(
                    category_summary,
                    name_key="Category",
                    value_key="Count"
                )

                if category_rows:
                    category_fig = px.bar(
                        category_rows,
                        x="Category",
                        y="Count",
                        color="Category",
                        title="Complaints by Category",
                        template="plotly_dark"
                    )
                    st.plotly_chart(
                        category_fig,
                        use_container_width=True
                    )
                else:
                    show_admin_table_or_message(
                        category_summary,
                        "No category summary is available yet."
                    )

                st.subheader("⚠️ Severity Distribution")

                severity_summary = data.get("severity_summary", {})
                severity_rows = to_chart_rows(
                    severity_summary,
                    name_key="Severity",
                    value_key="Count"
                )

                if severity_rows:
                    severity_fig = px.pie(
                        severity_rows,
                        names="Severity",
                        values="Count",
                        title="Complaints by Severity",
                        template="plotly_dark"
                    )
                    st.plotly_chart(
                        severity_fig,
                        use_container_width=True
                    )
                else:
                    show_admin_table_or_message(
                        severity_summary,
                        "No severity summary is available yet."
                    )

                st.divider()
                st.subheader("🔁 Recurring Complaint Categories")
                show_admin_table_or_message(
                    data.get("recurring_categories", []),
                    "No recurring categories were identified yet."
                )

                st.subheader("📍 Recurring Complaint Areas")
                show_admin_table_or_message(
                    data.get("recurring_areas", []),
                    "No recurring areas were identified yet."
                )

                st.subheader("🚨 Unresolved High-Severity Complaints")
                show_admin_table_or_message(
                    high_priority,
                    "No unresolved high-priority complaints were returned."
                )

                st.divider()
                st.subheader("💡 Administrative Recommendations")

                recommendations = data.get(
                    "admin_recommendations", []
                )

                if isinstance(recommendations, list) and recommendations:
                    for recommendation in recommendations:
                        if isinstance(recommendation, dict):
                            st.info(
                                recommendation.get("recommendation")
                                or recommendation.get("message")
                                or str(recommendation)
                            )
                        else:
                            st.info(str(recommendation))
                elif isinstance(recommendations, str) and recommendations.strip():
                    st.info(recommendations)
                else:
                    st.info("No recommendations are available yet.")

                with st.expander("View complete AI Insights response"):
                    st.json(data)

                if st.button("🔄 Refresh AI Insights"):
                    st.rerun()

            except requests.RequestException as error:
                show_api_error(error)
            except (ValueError, TypeError) as error:
                st.error(f"Could not display AI Insights: {error}")


    # ---------------- HISTORICAL TRENDS (ADMIN) ----------------

    elif selected_page == "Historical Trends":

        st.title("📈 Historical Complaint Trends")
        st.write(
            "Explore how civic complaints change over time, "
            "including daily activity, monthly activity, and categories."
        )

        if role != "admin":
            st.error("Administrator access is required to view Historical Trends.")
        else:
            try:
                response_data = get_admin_data(
                    "/admin/historical-trends"
                )

                # The backend returns the historical data inside "trends".
                trends = response_data.get("trends", response_data)

                st.success("Historical Trends loaded successfully.")

                if not isinstance(trends, dict):
                    st.warning(
                        "The backend returned an unexpected trends format."
                    )
                    st.json(response_data)
                else:
                    # Show numeric summary values when available.
                    summary_values = []
                    for key, value in trends.items():
                        if isinstance(value, (int, float)):
                            summary_values.append((key, value))

                    if summary_values:
                        metric_columns = st.columns(
                            min(4, len(summary_values))
                        )
                        for index, (key, value) in enumerate(
                            summary_values[:4]
                        ):
                            metric_columns[index].metric(
                                key.replace("_", " ").title(),
                                value
                            )

                    st.divider()

                    # Detect common names used for daily trend arrays.
                    daily_data = None
                    for key in (
                        "daily_trends",
                        "daily",
                        "daily_complaints",
                        "daily_reports",
                        "complaints_by_day"
                    ):
                        if key in trends:
                            daily_data = trends[key]
                            break

                    st.subheader("📅 Daily Complaint Trends")
                    daily_rows = to_chart_rows(
                        daily_data,
                        name_key="Date",
                        value_key="Complaints"
                    )

                    if daily_rows:
                        daily_fig = px.line(
                            daily_rows,
                            x="Date",
                            y="Complaints",
                            markers=True,
                            title="Complaints Recorded by Day",
                            template="plotly_dark"
                        )
                        st.plotly_chart(
                            daily_fig,
                            use_container_width=True
                        )
                    else:
                        st.info(
                            "Daily trend data is not available or "
                            "there are not enough records yet."
                        )

                    # Detect common names used for monthly trend arrays.
                    monthly_data = None
                    for key in (
                        "monthly_trends",
                        "monthly",
                        "monthly_complaints",
                        "monthly_reports",
                        "complaints_by_month"
                    ):
                        if key in trends:
                            monthly_data = trends[key]
                            break

                    st.subheader("🗓️ Monthly Complaint Trends")
                    monthly_rows = to_chart_rows(
                        monthly_data,
                        name_key="Month",
                        value_key="Complaints"
                    )

                    if monthly_rows:
                        monthly_fig = px.bar(
                            monthly_rows,
                            x="Month",
                            y="Complaints",
                            title="Complaints Recorded by Month",
                            color="Month",
                            template="plotly_dark"
                        )
                        st.plotly_chart(
                            monthly_fig,
                            use_container_width=True
                        )
                    else:
                        st.info(
                            "Monthly trend data is not available yet."
                        )

                    # Detect common names used for category trends.
                    category_data = None
                    for key in (
                        "category_trends",
                        "category_summary",
                        "categories",
                        "complaints_by_category"
                    ):
                        if key in trends:
                            category_data = trends[key]
                            break

                    st.subheader("🏷️ Complaint Category Trends")
                    category_rows = to_chart_rows(
                        category_data,
                        name_key="Category",
                        value_key="Complaints"
                    )

                    if category_rows:
                        category_fig = px.bar(
                            category_rows,
                            x="Category",
                            y="Complaints",
                            color="Category",
                            title="Complaints by Category",
                            template="plotly_dark"
                        )
                        st.plotly_chart(
                            category_fig,
                            use_container_width=True
                        )
                    else:
                        st.info(
                            "Category trend data is not available yet."
                        )

                    st.divider()
                    st.subheader("📋 Historical Data")

                    displayed_known_keys = {
                        "daily_trends", "daily", "daily_complaints",
                        "daily_reports", "complaints_by_day",
                        "monthly_trends", "monthly", "monthly_complaints",
                        "monthly_reports", "complaints_by_month",
                        "category_trends", "category_summary",
                        "categories", "complaints_by_category"
                    }

                    remaining_data = {
                        key: value
                        for key, value in trends.items()
                        if key not in displayed_known_keys
                    }

                    if remaining_data:
                        st.json(remaining_data)

                    with st.expander("View complete Historical Trends response"):
                        st.json(response_data)

                if st.button("🔄 Refresh Historical Trends"):
                    st.rerun()

            except requests.RequestException as error:
                show_api_error(error)
            except (ValueError, TypeError, KeyError) as error:
                st.error(
                    f"Could not display Historical Trends: {error}"
                )


# ---------------- FOOTER ----------------

st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color:#55dcff;">
        <b>CivicPulse AI</b><br>
        Intelligent Smart City Complaint Management<br>
        <small>AI-assisted civic issue reporting and analytics</small>
    </div>
    """,
    unsafe_allow_html=True
)
