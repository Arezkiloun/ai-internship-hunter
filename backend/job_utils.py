import re
import unicodedata


def normalize_text(value):
    value = value or ""

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(
        value.split()
    )


def is_target_location(job):
    location = normalize_text(
        job.get("location", "")
    )

    title = normalize_text(
        job.get("title", "")
    )

    text = f"{location} {title}"

    # Zones explicitement exclues
    excluded = [
        "canada",
        "montreal",
        "lyon",
        "marseille",
        "toulouse",
        "bordeaux",
        "lille",
        "nantes",
        "nice",
        "strasbourg",
        "rennes",
    ]

    if any(
        place in text
        for place in excluded
    ):
        return False

    accepted = [
        "paris",
        "ile de france",
        "hauts de seine",
        "seine saint denis",
        "val de marne",
        "val d oise",
        "yvelines",
        "essonne",
        "seine et marne",
        "rouen",
        "seine maritime",
        "petit quevilly",
    ]

    if any(
        place in text
        for place in accepted
    ):
        return True

    # Départements Île-de-France
    department_patterns = [
        r"\b75\b",
        r"\b77\b",
        r"\b78\b",
        r"\b91\b",
        r"\b92\b",
        r"\b93\b",
        r"\b94\b",
        r"\b95\b",
        r"\b76\b",
    ]

    return any(
        re.search(pattern, text)
        for pattern in department_patterns
    )


def canonical_job_key(job):
    title = normalize_text(
        job.get("title", "")
    )

    company = normalize_text(
        job.get("company", "")
    )

    # Enlève quelques mots qui créent de faux doublons.
    noise = [
        "h f",
        "f h",
        "stage",
        "stagiaire",
        "intern",
        "internship",
    ]

    for word in noise:
        title = re.sub(
            rf"\b{re.escape(word)}\b",
            " ",
            title
        )

    title = " ".join(
        title.split()
    )

    return (
        company,
        title
    )
