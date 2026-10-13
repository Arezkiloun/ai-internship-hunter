import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv(".env")

CLIENT_ID = os.getenv("FT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET")

TOKEN_URL = (
    "https://entreprise.francetravail.fr/"
    "connexion/oauth2/access_token?realm=%2Fpartenaire"
)

SEARCH_URL = (
    "https://api.francetravail.io/"
    "partenaire/offresdemploi/v2/offres/search"
)


def get_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "FT_CLIENT_ID et FT_CLIENT_SECRET manquants dans .env"
        )

    response = requests.post(
        TOKEN_URL,
        headers={
            "Content-Type":
            "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "api_offresdemploiv2 o2dsoffre"
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()["access_token"]


def request_with_retry(headers, params, retries=3):
    for attempt in range(retries):
        response = requests.get(
            SEARCH_URL,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code == 204:
            return None

        if response.status_code == 429:
            wait_time = 5 * (attempt + 1)

            print(
                f"⚠️ France Travail limite les requêtes. "
                f"Attente {wait_time}s..."
            )

            time.sleep(wait_time)
            continue

        response.raise_for_status()
        return response

    print(
        "⚠️ Département ignoré après plusieurs erreurs 429 :",
        params.get("departement")
    )

    return None


def fetch_jobs():
    token = get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    searches = [
        {
            "motsCles": "développeur stage",
            "departement": "75",
            "range": "0-49"
        },
        {
            "motsCles": "développeur stage",
            "departement": "92",
            "range": "0-49"
        },
        {
            "motsCles": "développeur stage",
            "departement": "93",
            "range": "0-49"
        },
        {
            "motsCles": "développeur stage",
            "departement": "94",
            "range": "0-49"
        },
        {
            "motsCles": "développeur stage",
            "departement": "76",
            "range": "0-49"
        }
    ]

    jobs = []
    seen = set()

    for params in searches:
        response = request_with_retry(
            headers,
            params
        )

        if response is None:
            time.sleep(2)
            continue

        data = response.json()

        for item in data.get("resultats", []):
            job_id = item.get("id")

            if job_id in seen:
                continue

            seen.add(job_id)

            company = (
                item.get("entreprise", {})
                .get("nom", "Entreprise inconnue")
            )

            location = (
                item.get("lieuTravail", {})
                .get("libelle", "")
            )

            url = ""

            origine = item.get("origineOffre", {})
            partenaires = origine.get("partenaires", [])

            if partenaires:
                url = partenaires[0].get(
                    "urlOrigine", ""
                )

            jobs.append({
                "title": item.get(
                    "intitule", ""
                ),
                "company": company,
                "location": location,
                "description": item.get(
                    "description", ""
                ),
                "skills": [],
                "url": url,
                "remote": False,
                "source": "France Travail"
            })

        # Pause entre deux départements
        time.sleep(2)

    return jobs


def extract_duration_months(job):
    text = (
        job.get("title", "")
        + " "
        + job.get("description", "")
    ).lower()

    patterns = [
        r"(\d+)\s*mois",
        r"durée\s*[:\-]?\s*(\d+)\s*mois",
        r"stage\s+de\s+(\d+)\s*mois"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

    return None


def is_relevant(job):
    title = job.get("title", "").lower()

    internship_keywords = [
        "stage",
        "stagiaire",
        "intern",
        "internship"
    ]

    if not any(
        keyword in title
        for keyword in internship_keywords
    ):
        return False

    development_keywords = [
        "développeur",
        "developer",
        "software",
        "fullstack",
        "full-stack",
        "full stack",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "web",
        "logiciel"
    ]

    if not any(
        keyword in title
        for keyword in development_keywords
    ):
        return False

    excluded_keywords = [
        "senior",
        "lead",
        "manager",
        "director",
        "directeur",
        "principal",
        "chief"
    ]

    if any(
        keyword in title
        for keyword in excluded_keywords
    ):
        return False

    duration = extract_duration_months(job)

    if duration is not None:
        if duration < 4 or duration > 6:
            return False

    return True
