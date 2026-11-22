CivicPulse AI 🏙️

An AI-powered civic complaint management platform designed to help citizens report public infrastructure issues and help administrators analyze, prioritize, and manage complaints.

📸 Project Screenshots

Dashboard

"CivicPulse AI Dashboard" (screenshots/dashboard.png)

AI Insights

"AI Insights" (screenshots/ai_insights.png)

Live Complaint Map

"Live Complaint Map" (screenshots/live_map.png)

3D Smart City

"3D Smart City" (screenshots/smart_city_3d.png)

Complaint Management

"All Complaints" (screenshots/all_complaints.png)

AI Complaint Analysis

"AI Analysis" (screenshots/ai_analysis.png)

✨ Features

- Citizen registration and login
- Administrator authentication and role-based access
- Civic complaint submission and management
- AI-assisted complaint classification
- Severity and priority assessment
- Duplicate complaint detection using TF-IDF and cosine similarity
- Image analysis using CLIP
- Interactive complaint map
- 3D Smart City visualization
- Admin analytics dashboard
- AI-generated analytical insights using rule-based logic
- Historical complaint trends
- Complaint status tracking
- SQLite database

🛠️ Tech Stack

Frontend

- Python
- Streamlit
- HTML
- Interactive visualizations

Backend

- FastAPI
- REST API
- JWT authentication

Database

- SQLite

AI / Machine Learning

- Scikit-learn
- TF-IDF
- Cosine Similarity
- CLIP
- Transformers
- PyTorch

📂 Project Structure

CivicPulseAI/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── database_backup.py
│   ├── duplicate_detector.py
│   ├── image_analyzer.py
│   └── requirements.txt
│
├── frontend/
│   ├── app.py
│   ├── city_preview.py
│   └── smart_city.html
│
├── screenshots/
│   ├── dashboard.png
│   ├── ai_insights.png
│   ├── live_map.png
│   ├── smart_city_3d.png
│   ├── all_complaints.png
│   └── ai_analysis.png
│
├── .gitignore
└── README.md

🚀 Running the Project

1. Clone the repository

git clone https://github.com/mehaknaaz45623-hub/CivicPulseAI.git
cd CivicPulseAI

2. Install backend dependencies

cd backend
pip install -r requirements.txt

3. Start the backend

uvicorn main:app --reload

The backend API will run locally. Interactive API documentation is available at:

"http://127.0.0.1:8000/docs"

4. Start the frontend

Open a second terminal:

cd frontend
streamlit run app.py

🎯 Project Goal

CivicPulse AI aims to improve civic issue reporting and management through technology, data analysis, visualizations, and AI-assisted tools.

👩‍💻 Developer

Mehak Naaz

GitHub: "mehaknaaz45623-hub" (https://github.com/mehaknaaz45623-hub)

---

Built as an AI-focused civic technology project.