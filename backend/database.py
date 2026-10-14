import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent

load_dotenv(ROOT_DIR / ".env.local")
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquante")


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    score INTEGER,
                    status TEXT NOT NULL DEFAULT 'found',
                    source TEXT,
                    UNIQUE(title, company)
                )
            """)

            cursor.execute("""
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS source TEXT
            """)


def save_job(job, score):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO jobs (
                    title,
                    company,
                    location,
                    description,
                    url,
                    score,
                    source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (title, company)
                DO NOTHING
                RETURNING id
            """, (
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("description"),
                job.get("url", ""),
                score,
                job.get("source"),
            ))

            row = cursor.fetchone()

    if row is None:
        return None, False

    return row["id"], True


def get_jobs():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    title,
                    company,
                    location,
                    url,
                    score,
                    status,
                    source
                FROM jobs
                ORDER BY score DESC, id DESC
            """)

            return cursor.fetchall()


def update_job_status(job_id, status):
    allowed_statuses = [
        "found",
        "applied",
        "interview",
        "rejected",
        "accepted",
    ]

    if status not in allowed_statuses:
        return False

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE jobs
                SET status = %s
                WHERE id = %s
            """, (status, job_id))

            return cursor.rowcount > 0


def get_job_by_id(job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    title,
                    company,
                    location,
                    description,
                    url,
                    score,
                    status,
                    source
                FROM jobs
                WHERE id = %s
            """, (job_id,))

            return cursor.fetchone()


def init_applications_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id BIGSERIAL PRIMARY KEY,
                    job_id BIGINT NOT NULL UNIQUE
                        REFERENCES jobs(id) ON DELETE CASCADE,
                    subject TEXT NOT NULL,
                    email_body TEXT NOT NULL,
                    linkedin_message TEXT,
                    strengths TEXT,
                    model_used TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMPTZ,
                    follow_up_at TIMESTAMPTZ
                )
            """)


def save_application(job_id, application):
    strengths = json.dumps(
        application.get("strengths", []),
        ensure_ascii=False,
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO applications (
                    job_id,
                    subject,
                    email_body,
                    linkedin_message,
                    strengths,
                    model_used
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id)
                DO UPDATE SET
                    subject = EXCLUDED.subject,
                    email_body = EXCLUDED.email_body,
                    linkedin_message = EXCLUDED.linkedin_message,
                    strengths = EXCLUDED.strengths,
                    model_used = EXCLUDED.model_used,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                job_id,
                application.get("subject", ""),
                application.get("email_body", ""),
                application.get("linkedin_message", ""),
                strengths,
                application.get("model_used", ""),
            ))


def _decode_strengths(item):
    if item is None:
        return None

    try:
        item["strengths"] = json.loads(
            item.get("strengths") or "[]"
        )
    except (json.JSONDecodeError, TypeError):
        item["strengths"] = []

    return item


def get_application(job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    job_id,
                    subject,
                    email_body,
                    linkedin_message,
                    strengths,
                    model_used,
                    created_at,
                    updated_at,
                    sent_at,
                    follow_up_at
                FROM applications
                WHERE job_id = %s
            """, (job_id,))

            row = cursor.fetchone()

    return _decode_strengths(row)


def delete_application(job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM applications
                WHERE job_id = %s
            """, (job_id,))

            return cursor.rowcount > 0


def ensure_application_tracking_columns():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE applications
                ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ
            """)


def ensure_follow_up_column():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE applications
                ADD COLUMN IF NOT EXISTS follow_up_at TIMESTAMPTZ
            """)


def get_all_applications():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    a.id,
                    a.job_id,
                    a.subject,
                    a.email_body,
                    a.linkedin_message,
                    a.strengths,
                    a.model_used,
                    a.created_at,
                    a.updated_at,
                    a.sent_at,
                    a.follow_up_at,
                    j.title,
                    j.company,
                    j.location,
                    j.url,
                    j.score,
                    j.status,
                    j.source
                FROM applications a
                JOIN jobs j
                    ON j.id = a.job_id
                ORDER BY a.updated_at DESC
            """)

            rows = cursor.fetchall()

    return [
        _decode_strengths(row)
        for row in rows
    ]


def mark_application_sent(job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE applications
                SET
                    sent_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s
            """, (job_id,))

            return cursor.rowcount > 0


def schedule_follow_up(job_id, days=7):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE applications
                SET
                    follow_up_at = CURRENT_TIMESTAMP
                        + (%s * INTERVAL '1 day'),
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s
            """, (days, job_id))

            return cursor.rowcount > 0


def clear_follow_up(job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE applications
                SET
                    follow_up_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s
            """, (job_id,))

            return cursor.rowcount > 0
