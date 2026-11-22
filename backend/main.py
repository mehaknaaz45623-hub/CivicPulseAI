import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import (
    FastAPI, HTTPException, Depends, UploadFile, File
)
from fastapi.security import (
    OAuth2PasswordBearer, OAuth2PasswordRequestForm
)
from pydantic import BaseModel, EmailStr
from pwdlib import PasswordHash
from jose import JWTError, jwt

from database import initialize_database, get_connection
from ai_classifier import classify_complaint
from duplicate_detector import find_similar_reports
from image_analyzer import analyze_image_bytes
from analytics import (
    get_dashboard_analytics,
    get_historical_trends
)
from ai_insights import get_ai_insights


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from backend/.env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

app = FastAPI(
    title="CivicPulse AI",
    description="AI-powered Smart City Complaint Management System",
    version="2.8.0"
)


@app.on_event("startup")
def startup():
    initialize_database()


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class ReportCreate(BaseModel):
    title: str
    description: str
    latitude: float | None = None
    longitude: float | None = None


class StatusUpdate(BaseModel):
    status: str


class ClassificationRequest(BaseModel):
    title: str
    description: str


def create_access_token(user_id: int, role: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }

    return jwt.encode(
        payload, SECRET_KEY, algorithm=ALGORITHM
    )


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    connection = get_connection()

    try:
        user = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if user is None:
            raise credentials_exception

        return dict(user)

    finally:
        connection.close()


def require_admin(current_user=Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    return current_user


@app.get("/")
def home():
    return {
        "message": "Welcome to CivicPulse AI",
        "status": "Running",
        "version": "2.8.0"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/auth/register", status_code=201)
def register_user(data: UserRegister):
    name = data.name.strip()
    email = str(data.email).strip().lower()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty"
        )

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    hashed_password = password_hash.hash(data.password)
    connection = get_connection()

    try:
        existing_user = connection.execute(
            "SELECT id FROM users WHERE LOWER(email) = ?",
            (email,)
        ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email is already registered"
            )

        cursor = connection.execute(
            """
            INSERT INTO users
            (name, email, hashed_password, role)
            VALUES (?, ?, ?, 'citizen')
            """,
            (name, email, hashed_password)
        )

        connection.commit()

        return {
            "message": "Registration successful",
            "user_id": cursor.lastrowid
        }

    finally:
        connection.close()


@app.post("/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    email = form_data.username.strip().lower()
    password = form_data.password
    connection = get_connection()

    try:
        user = connection.execute(
            "SELECT * FROM users WHERE LOWER(email) = ?",
            (email,)
        ).fetchone()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )

        try:
            valid = password_hash.verify(
                password, user["hashed_password"]
            )
        except Exception:
            valid = False

        if not valid:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )

        token = create_access_token(
            user["id"], user["role"]
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    finally:
        connection.close()


@app.get("/auth/me")
def get_my_profile(current_user=Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"]
    }


@app.post("/reports", status_code=201)
def create_report(
    data: ReportCreate,
    current_user=Depends(get_current_user)
):
    title = data.title.strip()
    description = data.description.strip()

    if not title or not description:
        raise HTTPException(
            status_code=400,
            detail="Title and description are required"
        )

    ai_result = classify_complaint(title, description)

    try:
        similar_reports = find_similar_reports(
            title, description
        )
    except Exception as error:
        print("Duplicate detection warning:", error)
        similar_reports = []

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO reports (
                title, category, description,
                latitude, longitude, user_id,
                severity, ai_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                ai_result["category"],
                description,
                data.latitude,
                data.longitude,
                current_user["id"],
                ai_result["severity"],
                ai_result["confidence"]
            )
        )

        connection.commit()

        return {
            "message": "Complaint submitted successfully",
            "report_id": cursor.lastrowid,
            "ai_analysis": ai_result,
            "possible_duplicates": similar_reports
        }

    finally:
        connection.close()


@app.get("/reports")
def get_reports(current_user=Depends(get_current_user)):
    connection = get_connection()

    try:
        if current_user["role"] == "admin":
            reports = connection.execute(
                "SELECT * FROM reports ORDER BY id DESC"
            ).fetchall()
        else:
            reports = connection.execute(
                """
                SELECT * FROM reports
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (current_user["id"],)
            ).fetchall()

        return [dict(report) for report in reports]

    finally:
        connection.close()


@app.get("/reports/{report_id}")
def get_report(
    report_id: int,
    current_user=Depends(get_current_user)
):
    connection = get_connection()

    try:
        report = connection.execute(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,)
        ).fetchone()

        if report is None:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )

        if (
            current_user["role"] != "admin"
            and report["user_id"] != current_user["id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="You cannot access this report"
            )

        return dict(report)

    finally:
        connection.close()


@app.patch("/reports/{report_id}/status")
def update_report_status(
    report_id: int,
    data: StatusUpdate,
    admin=Depends(require_admin)
):
    allowed_statuses = [
        "Pending", "In Progress", "Resolved"
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    connection = get_connection()

    try:
        report = connection.execute(
            "SELECT id FROM reports WHERE id = ?",
            (report_id,)
        ).fetchone()

        if report is None:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )

        connection.execute(
            "UPDATE reports SET status = ? WHERE id = ?",
            (data.status, report_id)
        )

        connection.commit()

        return {
            "message": "Report status updated successfully",
            "report_id": report_id,
            "new_status": data.status
        }

    finally:
        connection.close()


@app.post("/ai/classify")
def classify_report(
    data: ClassificationRequest,
    current_user=Depends(get_current_user)
):
    return classify_complaint(
        data.title, data.description
    )


@app.post("/ai/check-duplicates")
def check_duplicates(
    data: ClassificationRequest,
    current_user=Depends(get_current_user)
):
    if not data.title.strip() or not data.description.strip():
        raise HTTPException(
            status_code=400,
            detail="Title and description are required"
        )

    try:
        matches = find_similar_reports(
            data.title.strip(),
            data.description.strip()
        )

        return {
            "message": "Duplicate check completed",
            "possible_duplicates": matches,
            "matches_found": len(matches)
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Duplicate detection failed"
        )


@app.post("/ai/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    try:
        image_bytes = await image.read(5 * 1024 * 1024 + 1)

        result = analyze_image_bytes(image_bytes)

        return {
            "message": "AI image analysis completed",
            "filename": image.filename,
            "analysis": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print("Image analysis error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Image analysis failed. Check the backend terminal."
        )

    finally:
        await image.close()


@app.get("/admin/analytics")
def admin_analytics(admin=Depends(require_admin)):
    return {
        "message": "Admin analytics retrieved successfully",
        "analytics": get_dashboard_analytics()
    }


@app.get("/admin/ai-insights")
def admin_ai_insights(admin=Depends(require_admin)):
    try:
        insights = get_ai_insights()

        return {
            "message": "AI insights retrieved successfully",
            **insights
        }

    except Exception as error:
        print("AI insights error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve AI insights"
        )


# ---------------- HISTORICAL TRENDS API ----------------

@app.get("/admin/historical-trends")
def admin_historical_trends(admin=Depends(require_admin)):
    try:
        trends = get_historical_trends()

        return {
            "message": "Historical trends retrieved successfully",
            "trends": trends
        }

    except Exception as error:
        print("Historical trends error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve historical trends"
        )