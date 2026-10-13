import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

print("\n🚀 AI INTERNSHIP HUNTER — CHECK V1\n")

# -------------------------
# ENV
# -------------------------

required_env = [
    "GEMINI_API_KEY",
    "FT_CLIENT_ID",
    "FT_CLIENT_SECRET",
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
]

print("🔐 Variables API")

env_ok = True

for name in required_env:
    if os.getenv(name):
        print(f"✅ {name}")
    else:
        print(f"❌ {name} manquante")
        env_ok = False


# -------------------------
# FILES
# -------------------------

print("\n📁 Fichiers")

required_files = [
    "main.py",
    "database.py",
    "matching.py",
    "ai_generator.py",
    "job_utils.py",
    "profile/profile.json",
    "sources/arbeitnow.py",
    "sources/france_travail.py",
    "sources/adzuna.py",
]

files_ok = True

for filename in required_files:
    if Path(filename).exists():
        print(f"✅ {filename}")
    else:
        print(f"❌ {filename}")
        files_ok = False


# -------------------------
# DATABASE
# -------------------------

print("\n🗄️ Base de données")

db_ok = True

try:
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")
    jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    applications = cursor.fetchone()[0]

    print(f"✅ Offres enregistrées : {jobs}")
    print(f"✅ Candidatures : {applications}")

    cursor.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE title LIKE '%Canada%'
    """)

    outside = cursor.fetchone()[0]

    if outside == 0:
        print("✅ Pas d'offres Canada")
    else:
        print(f"⚠️ Offres Canada restantes : {outside}")

    cursor.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE source IS NULL OR source = ''
    """)

    missing_source = cursor.fetchone()[0]

    if missing_source == 0:
        print("✅ Toutes les offres ont une source")
    else:
        print(
            f"⚠️ Offres sans source : {missing_source}"
        )

    conn.close()

except Exception as e:
    db_ok = False
    print("❌ Erreur DB :", e)


# -------------------------
# GIT SECURITY
# -------------------------

print("\n🛡️ Sécurité")

gitignore = Path(".gitignore")

security_ok = True

if gitignore.exists():
    content = gitignore.read_text()

    if ".env" in content:
        print("✅ .env ignoré par Git")
    else:
        print("❌ .env absent de .gitignore")
        security_ok = False

else:
    print("❌ .gitignore absent")
    security_ok = False


# -------------------------
# FINAL
# -------------------------

print("\n-----------------------------")

if (
    env_ok
    and files_ok
    and db_ok
    and security_ok
):
    print("✅ V1 prête pour les tests finaux")
else:
    print("⚠️ V1 nécessite encore des corrections")

print("-----------------------------\n")
