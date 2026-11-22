CivicPulse AI 🏙️

AI-Powered Smart City Complaint Management System

CivicPulse AI is an intelligent civic complaint management platform designed to help citizens report public issues and help administrators analyze, prioritize, and manage complaints efficiently.

The platform combines complaint management, AI-powered classification, duplicate detection, priority analysis, analytics, and a futuristic 3D smart city visualization.

✨ Features

👤 Citizen Portal

- Citizen registration and secure login
- Submit civic complaints
- AI-powered complaint classification
- Severity and priority assessment
- Duplicate complaint detection
- Track complaint status
- View personal complaints

🛡️ Admin Portal

- Admin authentication
- View and manage all complaints
- Update complaint statuses
- Monitor complaint statistics
- Analyze complaint categories and severity
- View AI-generated analytical insights
- Explore historical complaint trends

🤖 AI Capabilities

- Automatic complaint category classification
- Severity assessment
- Priority scoring
- Duplicate complaint detection using TF-IDF and cosine similarity
- Image analysis using CLIP
- AI-powered civic insights and recommendations

📊 Visualization

- Interactive analytics dashboard
- Complaint statistics and charts
- Historical trends
- Live complaint map
- 3D Smart City visualization

🛠️ Tech Stack

Technology| Purpose
Python| Core programming language
Streamlit| Frontend
FastAPI| Backend REST API
SQLite| Database
Scikit-learn| NLP and duplicate detection
Transformers| AI image analysis
CLIP| Image understanding
Plotly| Data visualization
JWT| Authentication

📁 Project Structure

CivicPulseAI/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── ai_classifier.py
│   ├── duplicate_detector.py
│   ├── image_analyzer.py
│   ├── analytics.py
│   ├── ai_insights.py
│   └── requirements.txt
│
├── frontend/
│   ├── app.py
│   └── [frontend assets]
│
├── .gitignore
└── README.md

🚀 Getting Started

1. Clone the repository

git clone https://github.com/YOUR_USERNAME/CivicPulseAI.git
cd CivicPulseAI

2. Setup the Backend

cd backend
pip install -r requirements.txt

Start the backend:

uvicorn main:app --reload

Backend API:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

3. Setup the Frontend

Open a second terminal and navigate to the frontend directory.

Start Streamlit:

streamlit run app.py

Frontend:

http://localhost:8501

🔍 How It Works

1. Citizens register and log in.
2. Citizens submit civic complaints.
3. AI analyzes the complaint and identifies its category and severity.
4. The system checks for similar existing complaints.
5. Complaints are stored in the database.
6. Administrators monitor complaints through the dashboard.
7. Administrators update complaint statuses.
8. Citizens track progress.
9. Analytics and AI insights help identify recurring civic issues.

🎯 Project Goal

The goal of CivicPulse AI is to make civic issue reporting more organized, data-driven, and transparent by combining AI-assisted analysis with an accessible complaint management system.

👩‍💻 Developer

Developed as an AI-powered smart city project.

---

CivicPulse AI — Smarter Cities, Better Communities.