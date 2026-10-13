from job_utils import is_target_location, canonical_job_key
from sources.adzuna import fetch_jobs as fetch_adzuna_jobs, is_relevant as adzuna_is_relevant
from database import init_applications_db, save_application, get_application, delete_application, ensure_application_tracking_columns, get_all_applications, mark_application_sent, ensure_follow_up_column, schedule_follow_up, clear_follow_up
from ai_generator import prepare_application, prepare_follow_up
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json

from matching import calculate_match
from database import init_db, save_job, get_jobs, update_job_status, get_job_by_id

from sources.arbeitnow import (
    fetch_jobs as fetch_arbeitnow_jobs,
    is_relevant as arbeitnow_is_relevant,
)

from sources.france_travail import (
    fetch_jobs as fetch_france_travail_jobs,
    is_relevant as france_travail_is_relevant,
)


app = FastAPI(
    title="AI Internship Hunter",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()
init_applications_db()
ensure_application_tracking_columns()
ensure_follow_up_column()


def load_profile():
    with open(
        "profile/profile.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


class JobOffer(BaseModel):
    title: str
    company: str
    location: str
    description: str
    skills: List[str] = []
    url: str = ""



class JobStatusUpdate(BaseModel):
    status: str


@app.get("/")
def home():
    return {
        "message": "AI Internship Hunter is running 🚀"
    }


@app.get("/profile")
def get_profile():
    return load_profile()


@app.post("/match")
def match_job(job: JobOffer):
    profile = load_profile()

    result = calculate_match(
        profile,
        job.model_dump()
    )

    return {
        "company": job.company,
        "title": job.title,
        "location": job.location,
        "match": result
    }


@app.post("/jobs")
def create_job(job: JobOffer):
    profile = load_profile()

    result = calculate_match(
        profile,
        job.model_dump()
    )

    job_id, created = save_job(
        job.model_dump(),
        result["score"]
    )

    return {
        "created": created,
        "id": job_id,
        "score": result["score"]
    }


@app.get("/jobs")
def list_jobs():
    return get_jobs()


@app.post("/fetch-jobs")
def fetch_arbeitnow():
    profile = load_profile()

    remote_jobs = fetch_arbeitnow_jobs()

    found = 0
    saved = 0
    best_jobs = []

    for job in remote_jobs:

        if not arbeitnow_is_relevant(job):
            continue

        found += 1

        result = calculate_match(
            profile,
            job
        )

        score = result["score"]

        job_id, created = save_job(
            job,
            score
        )

        if created:
            saved += 1

        best_jobs.append({
            "id": job_id,
            "source": "Arbeitnow",
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "score": score,
            "url": job["url"]
        })

    best_jobs.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "source": "Arbeitnow",
        "offers_received": len(remote_jobs),
        "relevant_offers": found,
        "new_offers_saved": saved,
        "best_matches": best_jobs[:10]
    }


@app.post("/fetch-france-travail")
def fetch_france_travail():
    profile = load_profile()

    remote_jobs = fetch_france_travail_jobs()

    saved = 0
    best_jobs = []

    for job in remote_jobs:

        if not france_travail_is_relevant(job):
            continue

        result = calculate_match(
            profile,
            job
        )

        score = result["score"]

        job_id, created = save_job(
            job,
            score
        )

        if created:
            saved += 1

        best_jobs.append({
            "id": job_id,
            "source": "France Travail",
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "score": score,
            "url": job["url"]
        })

    best_jobs.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "source": "France Travail",
        "offers_received": len(remote_jobs),
        "new_offers_saved": saved,
        "best_matches": best_jobs[:10]
    }


@app.post("/fetch-all")
def fetch_all():
    profile = load_profile()

    results = []
    total_saved = 0
    seen_jobs = set()

    # ------------------------
    # ARBEITNOW
    # ------------------------

    try:
        arbeitnow_jobs = fetch_arbeitnow_jobs()

        for job in arbeitnow_jobs:

            if not arbeitnow_is_relevant(job):
                continue

            if not is_target_location(job):
                continue

            job_key = canonical_job_key(job)

            if job_key in seen_jobs:
                continue

            seen_jobs.add(job_key)

            result = calculate_match(
                profile,
                job
            )

            score = result["score"]

            job_id, created = save_job(
                job,
                score
            )

            if not created:
                continue

            total_saved += 1

            results.append({
                "id": job_id,
                "source": "Arbeitnow",
                "company": job["company"],
                "title": job["title"],
                "location": job["location"],
                "score": score,
                "url": job["url"]
            })

    except Exception as e:
        results.append({
            "source": "Arbeitnow",
            "error": str(e)
        })

    # ------------------------
    # FRANCE TRAVAIL
    # ------------------------

    try:
        ft_jobs = fetch_france_travail_jobs()

        for job in ft_jobs:

            if not france_travail_is_relevant(job):
                continue

            if not is_target_location(job):
                continue

            job_key = canonical_job_key(job)

            if job_key in seen_jobs:
                continue

            seen_jobs.add(job_key)

            result = calculate_match(
                profile,
                job
            )

            score = result["score"]

            job_id, created = save_job(
                job,
                score
            )

            if not created:
                continue

            total_saved += 1

            results.append({
                "id": job_id,
                "source": "France Travail",
                "company": job["company"],
                "title": job["title"],
                "location": job["location"],
                "score": score,
                "url": job["url"]
            })

    except Exception as e:
        results.append({
            "source": "France Travail",
            "error": str(e)
        })

    # ------------------------
    # ADZUNA
    # ------------------------

    try:
        adzuna_jobs = fetch_adzuna_jobs()

        for job in adzuna_jobs:

            if not adzuna_is_relevant(job):
                continue

            if not is_target_location(job):
                continue

            job_key = canonical_job_key(job)

            if job_key in seen_jobs:
                continue

            seen_jobs.add(job_key)

            result = calculate_match(
                profile,
                job
            )

            score = result["score"]

            job_id, created = save_job(
                job,
                score
            )

            # Si l'offre existe déjà via une autre source,
            # on ne la recompte pas.
            if not created:
                continue

            total_saved += 1

            results.append({
                "id": job_id,
                "source": "Adzuna",
                "company": job["company"],
                "title": job["title"],
                "location": job["location"],
                "score": score,
                "url": job["url"]
            })

    except Exception as e:
        results.append({
            "source": "Adzuna",
            "error": str(e)
        })

    valid_results = [
        item
        for item in results
        if "score" in item
    ]

    valid_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    errors = [
        item
        for item in results
        if "error" in item
    ]

    return {
        "sources": [
            "Arbeitnow",
            "France Travail",
            "Adzuna"
        ],
        "new_offers_saved": total_saved,
        "best_matches": valid_results[:20],
        "errors": errors
    }


@app.patch("/jobs/{job_id}/status")
def change_job_status(
    job_id: int,
    data: JobStatusUpdate
):
    allowed = [
        "found",
        "applied",
        "interview",
        "rejected",
        "accepted"
    ]

    if data.status not in allowed:
        return {
            "success": False,
            "error": "Invalid status"
        }

    updated = update_job_status(
        job_id,
        data.status
    )

    return {
        "success": updated,
        "id": job_id,
        "status": data.status
    }


@app.get("/jobs/{job_id}/details")
def job_details(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return {
            "success": False,
            "error": "Job not found"
        }

    profile = load_profile()

    analysis_job = {
        "title": job["title"],
        "company": job["company"],
        "location": job["location"],
        "description": job["description"] or "",
        "skills": [],
        "url": job["url"] or ""
    }

    analysis = calculate_match(
        profile,
        analysis_job
    )

    return {
        "success": True,
        "job": job,
        "analysis": analysis
    }


@app.post("/jobs/{job_id}/prepare-application")
def prepare_job_application(job_id: int):
    try:
        job = get_job_by_id(job_id)

        if not job:
            return {
                "success": False,
                "error": "Offre introuvable"
            }

        with open(
            "profile/profile.json",
            "r",
            encoding="utf-8"
        ) as f:
            profile = json.load(f)

        application = prepare_application(
            profile,
            job
        )

        save_application(
            job_id,
            application
        )

        return {
            "success": True,
            "saved": True,
            "application": application
        }

    except Exception as e:
        print("ERREUR PREPARE APPLICATION:", repr(e))

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/jobs/{job_id}/application")
def read_saved_application(job_id: int):
    application = get_application(job_id)

    if not application:
        return {
            "success": False,
            "error": "Aucune candidature enregistrée"
        }

    return {
        "success": True,
        "application": application
    }


@app.delete("/jobs/{job_id}/application")
def delete_saved_application(job_id: int):
    deleted = delete_application(job_id)

    if not deleted:
        return {
            "success": False,
            "error": "Aucune candidature à supprimer"
        }

    return {
        "success": True
    }


@app.get("/applications")
def list_applications():
    return {
        "success": True,
        "applications": get_all_applications()
    }


@app.patch("/jobs/{job_id}/application/sent")
def set_application_sent(job_id: int):
    updated = mark_application_sent(job_id)

    if not updated:
        return {
            "success": False,
            "error": "Candidature introuvable"
        }

    update_job_status(
        job_id,
        "applied"
    )

    return {
        "success": True
    }


@app.patch("/jobs/{job_id}/application/follow-up")
def set_follow_up(job_id: int):
    updated = schedule_follow_up(
        job_id,
        7
    )

    if not updated:
        return {
            "success": False,
            "error": "Candidature introuvable"
        }

    return {
        "success": True
    }


@app.delete("/jobs/{job_id}/application/follow-up")
def delete_follow_up(job_id: int):
    updated = clear_follow_up(job_id)

    if not updated:
        return {
            "success": False,
            "error": "Candidature introuvable"
        }

    return {
        "success": True
    }


@app.post("/jobs/{job_id}/generate-follow-up")
def generate_follow_up(job_id: int):
    try:
        job = get_job_by_id(job_id)

        if not job:
            return {
                "success": False,
                "error": "Offre introuvable"
            }

        application = get_application(job_id)

        if not application:
            return {
                "success": False,
                "error": "Aucune candidature enregistrée"
            }

        profile = load_profile()

        follow_up = prepare_follow_up(
            profile,
            job,
            application
        )

        return {
            "success": True,
            "follow_up": follow_up
        }

    except Exception as e:
        print("ERREUR FOLLOW UP:", repr(e))

        return {
            "success": False,
            "error": str(e)
        }
