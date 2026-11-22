import re


CATEGORIES = {
    "Garbage": [
        "garbage", "waste", "trash", "rubbish",
        "dump", "dustbin", "litter", "dirty area",
        "overflowing garbage", "waste collection"
    ],
    "Road Damage": [
        "pothole", "road", "crack", "damaged road",
        "broken road", "pavement", "footpath",
        "road damage", "uneven road"
    ],
    "Streetlight": [
        "streetlight", "street light", "lamp",
        "dark road", "light not working",
        "broken street light", "no street lighting"
    ],
    "Water Supply": [
        "water leak", "leakage", "water pipe",
        "no water", "pipeline", "water shortage",
        "burst pipe", "water supply"
    ],
    "Drainage": [
        "drain", "sewage", "blocked drain",
        "overflow", "sewer", "drainage",
        "drain blockage", "waterlogging"
    ]
}


HIGH_RISK_WORDS = [
    "emergency",
    "dangerous",
    "accident",
    "life threatening",
    "major flooding",
    "burst pipe",
    "severe damage",
    "exposed wire",
    "electric shock",
    "fire hazard",
    "major collapse"
]


MEDIUM_RISK_WORDS = [
    "broken",
    "damaged",
    "blocked",
    "leaking",
    "overflow",
    "cracked",
    "not working",
    "waterlogging",
    "malfunctioning"
]


LOW_RISK_WORDS = [
    "minor",
    "small",
    "slightly",
    "routine"
]


def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def find_matches(text, keywords):
    return [
        word for word in keywords
        if re.search(
            r"(?<!\w)" + re.escape(word) + r"(?!\w)",
            text
        )
    ]


def classify_complaint(title, description):

    title = clean_text(title)
    description = clean_text(description)

    text = title + " " + description

    # Category detection
    scores = {}

    for category, keywords in CATEGORIES.items():
        scores[category] = sum(
            len(re.findall(re.escape(keyword), text))
            for keyword in keywords
        )

    best_category = max(scores, key=scores.get)
    total_matches = sum(scores.values())

    if scores[best_category] == 0:
        best_category = "Other"
        confidence = 0.0
    else:
        confidence = round(
            scores[best_category] / max(total_matches, 1),
            2
        )

    # Risk detection
    high_matches = find_matches(text, HIGH_RISK_WORDS)
    medium_matches = find_matches(text, MEDIUM_RISK_WORDS)
    low_matches = find_matches(text, LOW_RISK_WORDS)

    # Priority and severity estimation
    if high_matches:
        severity = "High"
        priority = "High"
        priority_score = 90

        explanation = (
            "High priority because potentially serious "
            "risk indicators were detected: "
            + ", ".join(high_matches)
        )

    elif medium_matches:
        severity = "Medium"
        priority = "Medium"
        priority_score = 60

        explanation = (
            "Medium priority because the complaint "
            "describes infrastructure or maintenance "
            "problems: "
            + ", ".join(medium_matches)
        )

    elif low_matches:
        severity = "Low"
        priority = "Low"
        priority_score = 30

        explanation = (
            "Low priority based on minor or routine "
            "issue indicators."
        )

    else:
        severity = "Low"
        priority = "Low"
        priority_score = 30

        explanation = (
            "No explicit high-risk or medium-risk "
            "indicators were detected. Manual review "
            "may still be necessary."
        )

    return {
        "category": best_category,
        "severity": severity,
        "confidence": confidence,
        "priority": priority,
        "priority_score": priority_score,
        "risk_indicators": high_matches + medium_matches,
        "explanation": explanation
    }