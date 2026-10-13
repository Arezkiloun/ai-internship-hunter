import json
import sqlite3


DB_NAME = "internships.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            url TEXT,
            score INTEGER,
            status TEXT DEFAULT 'found',
            UNIQUE(title, company)
        )
    """)

    conn.commit()
    conn.close()


def save_job(job, score):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO jobs (
                title,
                company,
                location,
                description,
                url,
                score
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("description"),
            job.get("url", ""),
            score
        ))

        conn.commit()

        job_id = cursor.lastrowid
        created = True

    except sqlite3.IntegrityError:
        job_id = None
        created = False

    conn.close()

    return job_id, created


def get_jobs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            company,
            location,
            url,
            score,
            status
        FROM jobs
        ORDER BY score DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def update_job_status(job_id, status):
    allowed_statuses = [
        "found",
        "applied",
        "interview",
        "rejected",
        "accepted"
    ]

    if status not in allowed_statuses:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET status = ?
        WHERE id = ?
        """,
        (status, job_id)
    )

    conn.commit()

    updated = cursor.rowcount > 0

    conn.close()

    return updated


def get_job_by_id(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            company,
            location,
            description,
            url,
            score,
            status
        FROM jobs
        WHERE id = ?
    """, (job_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def init_applications_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            subject TEXT NOT NULL,
            email_body TEXT NOT NULL,
            linkedin_message TEXT,
            strengths TEXT,
            model_used TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()


def save_application(job_id, application):
    conn = get_connection()
    cursor = conn.cursor()

    strengths = json.dumps(
        application.get("strengths", []),
        ensure_ascii=False
    )

    cursor.execute("""
        INSERT INTO applications (
            job_id,
            subject,
            email_body,
            linkedin_message,
            strengths,
            model_used
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(job_id)
        DO UPDATE SET
            subject = excluded.subject,
            email_body = excluded.email_body,
            linkedin_message = excluded.linkedin_message,
            strengths = excluded.strengths,
            model_used = excluded.model_used,
            updated_at = CURRENT_TIMESTAMP
    """, (
        job_id,
        application.get("subject", ""),
        application.get("email_body", ""),
        application.get("linkedin_message", ""),
        strengths,
        application.get("model_used", "")
    ))

    conn.commit()
    conn.close()


def get_application(job_id):
    conn = get_connection()
    cursor = conn.cursor()

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
            updated_at
        FROM applications
        WHERE job_id = ?
    """, (job_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    result = dict(row)

    try:
        result["strengths"] = json.loads(
            result.get("strengths") or "[]"
        )
    except json.JSONDecodeError:
        result["strengths"] = []

    return result


def delete_application(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM applications
        WHERE job_id = ?
    """, (job_id,))

    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()

    return deleted


def ensure_application_tracking_columns():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(applications)")
    columns = [
        row["name"] for row in cursor.fetchall()
    ]

    if "sent_at" not in columns:
        cursor.execute("""
            ALTER TABLE applications
            ADD COLUMN sent_at DATETIME
        """)

    conn.commit()
    conn.close()


def get_all_applications():
    conn = get_connection()
    cursor = conn.cursor()

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
            j.status
        FROM applications a
        JOIN jobs j
            ON j.id = a.job_id
        ORDER BY a.updated_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    results = []

    for row in rows:
        item = dict(row)

        try:
            item["strengths"] = json.loads(
                item.get("strengths") or "[]"
            )
        except json.JSONDecodeError:
            item["strengths"] = []

        results.append(item)

    return results


def mark_application_sent(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET sent_at = CURRENT_TIMESTAMP
        WHERE job_id = ?
    """, (job_id,))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def ensure_follow_up_column():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(applications)")
    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "follow_up_at" not in columns:
        cursor.execute("""
            ALTER TABLE applications
            ADD COLUMN follow_up_at DATETIME
        """)

    conn.commit()
    conn.close()


def schedule_follow_up(job_id, days=7):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET follow_up_at = datetime(
            'now',
            ? || ' days'
        )
        WHERE job_id = ?
    """, (
        str(days),
        job_id
    ))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def clear_follow_up(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET follow_up_at = NULL
        WHERE job_id = ?
    """, (job_id,))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def ensure_follow_up_column():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(applications)")
    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "follow_up_at" not in columns:
        cursor.execute("""
            ALTER TABLE applications
            ADD COLUMN follow_up_at DATETIME
        """)

    conn.commit()
    conn.close()


def schedule_follow_up(job_id, days=7):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET follow_up_at = datetime(
            'now',
            ? || ' days'
        )
        WHERE job_id = ?
    """, (
        str(days),
        job_id
    ))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def clear_follow_up(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET follow_up_at = NULL
        WHERE job_id = ?
    """, (job_id,))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def ensure_follow_up_column():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(applications)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "follow_up_at" not in columns:
        cursor.execute("""
            ALTER TABLE applications
            ADD COLUMN follow_up_at DATETIME
        """)

    conn.commit()
    conn.close()


def schedule_follow_up(job_id, days=7):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET follow_up_at = datetime(
            'now',
            ? || ' days'
        )
        WHERE job_id = ?
    """, (str(days), job_id))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def clear_follow_up(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET follow_up_at = NULL
        WHERE job_id = ?
    """, (job_id,))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated
