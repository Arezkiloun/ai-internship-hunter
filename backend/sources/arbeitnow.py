import requests
import re

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def clean_html(text):
    return re.sub(r"<[^>]+>", " ", text or "")


def fetch_jobs():
    response = requests.get(API_URL, timeout=20)
    response.raise_for_status()

    data = response.json()

    jobs = []

    for item in data.get("data", []):
        jobs.append({
            "title": item.get("title", ""),
            "company": item.get("company_name", ""),
            "location": item.get("location", ""),
            "description": clean_html(
                item.get("description", "")
            ),
            "skills": item.get("tags", []),
            "url": item.get("url", ""),
            "remote": item.get("remote", False)
        })

    return jobs


def contains_word(text, word):
    pattern = r"\b" + re.escape(word) + r"\b"
    return re.search(pattern, text, re.IGNORECASE) is not None


def is_relevant(job):
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()

    # 1. Exclure les postes trop expérimentés
    excluded = [
        "senior",
        "lead",
        "head",
        "director",
        "principal",
        "manager",
        "staff",
        "chief",
        "vp"
    ]

    if any(
        contains_word(title, word)
        for word in excluded
    ):
        return False

    # 2. Stage obligatoire dans le titre
    internship_patterns = [
        r"\bstage\b",
        r"\bstagiaire\b",
        r"\bintern\b",
        r"\binternship\b"
    ]

    is_internship = any(
        re.search(pattern, title, re.IGNORECASE)
        for pattern in internship_patterns
    )

    if not is_internship:
        return False

    # 3. Développement obligatoire dans le titre
    development_keywords = [
        "developer",
        "développeur",
        "software",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "fullstack",
        "full stack",
        "full-stack",
        "web developer",
        "software engineer"
    ]

    is_development = any(
        keyword in title
        for keyword in development_keywords
    )

    if not is_development:
        return False

    # 4. Localisation
    accepted_locations = [
        "paris",
        "île-de-france",
        "ile-de-france",
        "rouen",
        "france"
    ]

    location_ok = any(
        place in location
        for place in accepted_locations
    )

    if not location_ok:
        return False

    return True
