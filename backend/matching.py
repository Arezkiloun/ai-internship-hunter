import re
import unicodedata
from datetime import datetime, date


def normalize(text):
    text = text or ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    return text.lower().strip()


def contains_skill(skill, text):
    pattern = (
        r"(?<!\w)"
        + re.escape(skill)
        + r"(?!\w)"
    )

    return (
        re.search(
            pattern,
            text,
            re.IGNORECASE
        )
        is not None
    )


def extract_start_date(text):
    text = normalize(text)

    # 05/04/2027 ou 05-04-2027
    match = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b",
        text
    )

    if match:
        day, month, year = map(
            int,
            match.groups()
        )

        try:
            return date(
                year,
                month,
                day
            )
        except ValueError:
            pass

    months = {
        "janvier": 1,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "decembre": 12,
    }

    for month_name, month_number in months.items():
        match = re.search(
            rf"\b{month_name}\s+(20\d{{2}})\b",
            text
        )

        if match:
            year = int(match.group(1))

            return date(
                year,
                month_number,
                1
            )

    return None


def calculate_start_date_score(
    profile,
    job_text
):
    target_text = profile.get(
        "start_date"
    )

    if not target_text:
        return 0, "unknown", None

    try:
        target_date = datetime.strptime(
            target_text,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return 0, "unknown", None

    detected_date = extract_start_date(
        job_text
    )

    if detected_date is None:
        return 0, "unknown", None

    difference = abs(
        (
            detected_date
            - target_date
        ).days
    )

    if difference <= 31:
        return (
            5,
            "compatible",
            detected_date.isoformat()
        )

    if difference <= 62:
        return (
            3,
            "close",
            detected_date.isoformat()
        )

    return (
        0,
        "incompatible",
        detected_date.isoformat()
    )


def extract_duration(text):
    text = normalize(text)

    # Exemple : 4 à 6 mois
    match = re.search(
        r"\b(\d+)\s*(?:a|à|-)\s*(\d+)\s*mois\b",
        text
    )

    if match:
        return {
            "min": int(match.group(1)),
            "max": int(match.group(2)),
        }

    # Exemple : 6 mois
    match = re.search(
        r"\b(\d+)\s*mois\b",
        text
    )

    if match:
        months = int(
            match.group(1)
        )

        return {
            "min": months,
            "max": months,
        }

    return None


def calculate_duration_score(job_text):
    duration = extract_duration(
        job_text
    )

    if duration is None:
        return 0, "unknown", None

    minimum = duration["min"]
    maximum = duration["max"]

    # Parfait : durée entièrement comprise entre 4 et 6
    if (
        minimum >= 4
        and maximum <= 6
    ):
        return 5, "compatible", duration

    # Exemple 3 à 6 mois : compatible partiellement
    if (
        maximum >= 4
        and minimum <= 6
    ):
        return 3, "partial", duration

    return 0, "incompatible", duration


def calculate_match(profile, job):
    title = normalize(
        job.get("title", "")
    )

    location = normalize(
        job.get("location", "")
    )

    description = normalize(
        job.get("description", "")
    )

    skills_text = normalize(
        " ".join(
            job.get("skills", [])
        )
    )

    job_text = (
        title
        + " "
        + description
        + " "
        + skills_text
    )

    profile_skills = [
        normalize(skill)
        for skill in profile.get(
            "skills",
            []
        )
    ]

    matched_skills = []
    missing_skills = []

    for skill in profile_skills:
        if contains_skill(
            skill,
            job_text
        ):
            matched_skills.append(
                skill
            )
        else:
            missing_skills.append(
                skill
            )

    # --------------------
    # STAGE : 15
    # --------------------

    internship_score = 0

    internship_keywords = [
        "stage",
        "stagiaire",
        "intern",
        "internship",
    ]

    if any(
        keyword in title
        for keyword
        in internship_keywords
    ):
        internship_score = 15

    # --------------------
    # DEVELOPPEMENT : 15
    # --------------------

    development_score = 0

    development_keywords = [
        "developer",
        "developpeur",
        "software",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "fullstack",
        "full stack",
        "full-stack",
        "web",
        "logiciel",
        "ingenieur logiciel",
    ]

    if any(
        keyword in title
        for keyword
        in development_keywords
    ):
        development_score = 15

    # --------------------
    # LOCALISATION : 15
    # --------------------

    location_score = 0

    preferred_locations = [
        "paris",
        "ile-de-france",
        "ile de france",
        "rouen",
        "seine-maritime",
        "hauts-de-seine",
        "seine-saint-denis",
        "val-de-marne",
        "yvelines",
        "essonne",
        "val-d'oise",
        "seine-et-marne",
        "75 -",
        "76 -",
        "77 -",
        "78 -",
        "91 -",
        "92 -",
        "93 -",
        "94 -",
        "95 -",
    ]

    if any(
        preferred in location
        for preferred
        in preferred_locations
    ):
        location_score = 15

    elif "france" in location:
        location_score = 10

    elif (
        "remote" in location
        or "teletravail" in location
    ):
        location_score = 8

    # --------------------
    # JUNIOR / ETUDIANT : 10
    # --------------------

    junior_score = 0

    junior_keywords = [
        "junior",
        "student",
        "etudiant",
        "graduate",
        "intern",
        "stagiaire",
        "stage",
    ]

    if any(
        keyword in title
        for keyword
        in junior_keywords
    ):
        junior_score = 10

    # --------------------
    # COMPETENCES : 25
    # --------------------

    skills_score = min(
        len(matched_skills) * 5,
        25
    )

    # --------------------
    # FULL STACK / WEB : 10
    # --------------------

    fullstack_score = 0

    if any(
        keyword in title
        for keyword in [
            "fullstack",
            "full stack",
            "full-stack",
        ]
    ):
        fullstack_score = 10

    elif any(
        keyword in title
        for keyword in [
            "frontend",
            "front-end",
            "backend",
            "back-end",
            "web",
        ]
    ):
        fullstack_score = 5

    # --------------------
    # DATE : 5
    # --------------------

    (
        start_date_score,
        start_date_status,
        detected_start_date
    ) = calculate_start_date_score(
        profile,
        job_text
    )

    # --------------------
    # DUREE : 5
    # --------------------

    (
        duration_score,
        duration_status,
        detected_duration
    ) = calculate_duration_score(
        job_text
    )

    # --------------------
    # MALUS TECHNOLOGIES
    # --------------------

    penalty = 0
    penalties = []

    preferred_tech = [
        "react",
        "typescript",
        "javascript",
        "nestjs",
        "python",
    ]

    has_preferred_tech = any(
        contains_skill(
            tech,
            job_text
        )
        for tech in preferred_tech
    )

    # Java dominant
    if (
        any(
            keyword in title
            for keyword in [
                "java",
                "j2ee",
                "spring boot",
            ]
        )
        and not has_preferred_tech
    ):
        penalty -= 8
        penalties.append(
            "java_dominant"
        )

    # C / C++ dominant
    if (
        any(
            keyword in title
            for keyword in [
                "c++",
                "cplusplus",
                "developpeur c ",
                "developer c ",
            ]
        )
        and not has_preferred_tech
    ):
        penalty -= 10
        penalties.append(
            "c_cpp_dominant"
        )

    base_score = (
        internship_score
        + development_score
        + location_score
        + junior_score
        + skills_score
        + fullstack_score
        + start_date_score
        + duration_score
    )

    total_score = round(
        max(
            0,
            min(
                base_score + penalty,
                100
            )
        )
    )

    return {
        "score": total_score,

        "matched_skills": matched_skills,
        "missing_skills": missing_skills,

        "start_date": {
            "target": profile.get(
                "start_date"
            ),
            "detected": detected_start_date,
            "status": start_date_status,
        },

        "duration": {
            "detected": detected_duration,
            "status": duration_status,
        },

        "penalties": penalties,

        "details": {
            "internship": internship_score,
            "development": development_score,
            "location": location_score,
            "junior": junior_score,
            "skills": skills_score,
            "fullstack_bonus": fullstack_score,
            "start_date_bonus": start_date_score,
            "duration_bonus": duration_score,
            "penalty": penalty,
        },
    }
