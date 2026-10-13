import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/fr/search"

SEARCHES = [
    ("stage développeur", "Paris"),
    ("stage développeur", "Île-de-France"),
    ("stage développeur", "Rouen"),
    ("stage full stack", "Paris"),
    ("stage frontend", "Paris"),
    ("stage backend", "Paris"),
]


def fetch_jobs():
    if not APP_ID or not APP_KEY:
        raise RuntimeError(
            "ADZUNA_APP_ID ou ADZUNA_APP_KEY manquant dans .env"
        )

    jobs = []
    seen = set()

    for what, where in SEARCHES:
        response = requests.get(
            f"{BASE_URL}/1",
            params={
                "app_id": APP_ID,
                "app_key": APP_KEY,
                "results_per_page": 30,
                "what": what,
                "where": where,
                "content-type": "application/json",
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        for item in data.get("results", []):
            title = item.get("title", "").strip()

            company_data = item.get("company") or {}
            company = company_data.get(
                "display_name",
                "Entreprise inconnue"
            )

            location_data = item.get("location") or {}
            location = location_data.get(
                "display_name",
                ""
            )

            description = item.get(
                "description",
                ""
            )

            url = item.get(
                "redirect_url",
                ""
            )

            external_id = str(
                item.get("id", "")
            )

            unique_key = (
                external_id
                or f"{title}|{company}|{location}"
            )

            if unique_key in seen:
                continue

            seen.add(unique_key)

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "skills": [],
                "url": url,
                "remote": False,
                "source": "Adzuna",
                "external_id": external_id,
            })

    return jobs


def is_relevant(job):
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()

    excluded = [
        "senior",
        "lead",
        "manager",
        "director",
        "directeur",
        "principal",
        "head of",
        "staff engineer",
        "chief",
    ]

    if any(word in title for word in excluded):
        return False

    internship_words = [
        "stage",
        "stagiaire",
        "intern",
        "internship",
    ]

    if not any(
        word in title
        for word in internship_words
    ):
        return False

    dev_words = [
        "développeur",
        "developpeur",
        "developer",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "fullstack",
        "full-stack",
        "logiciel",
        "software",
        "web",
    ]

    if not any(
        word in title
        for word in dev_words
    ):
        return False

    # Écarte les stages explicitement trop courts ou trop longs.
    import re

    match = re.search(
        r"(\d+)\s*(?:mois|month)",
        title + " " + description
    )

    if match:
        months = int(match.group(1))

        if months < 4 or months > 6:
            return False

    return True
