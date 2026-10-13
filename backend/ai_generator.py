import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

load_dotenv(".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY manquante dans .env"
    )

client = genai.Client(
    api_key=API_KEY
)

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite"
]


def prepare_application(profile, job):
    prompt = f"""
Tu es un générateur de candidature de stage.

RÈGLE ABSOLUE :
N'invente aucune information sur le candidat.

PROFIL AUTORISÉ :
- Nom : {profile.get("name")}
- Actuellement en Bachelor 2 Informatique à EPITECH
- Recherche un stage développeur web / full-stack
- Début souhaité : {profile.get("start_date")}
- Durée : 4 à 6 mois
- Compétences : {", ".join(profile.get("skills", []))}
- Portfolio : {profile.get("portfolio")}
- GitHub : {profile.get("github")}
- A participé à des projets étudiants
- Peut mentionner un projet utilisant React, TypeScript, NestJS et PostgreSQL

INTERDIT :
- expérience professionnelle inventée
- entreprise précédente inventée
- nombre d'années d'expérience inventé
- responsabilité inventée
- compétence inventée
- expertise inventée
- dire que les études sont terminées
- transformer une exigence de l'offre en compétence du candidat
- utiliser le mot "maîtrise" pour une compétence
- dire "de nombreux projets"
- exagérer le niveau du candidat

PRÉFÈRE :
- "j'ai utilisé"
- "j'ai travaillé avec"
- "j'ai pratiqué"
- "dans mes projets étudiants"

OFFRE :
Entreprise : {job.get("company")}
Poste : {job.get("title")}
Lieu : {job.get("location")}

Description :
{job.get("description", "")}

Retourne uniquement du JSON valide :

{{
  "subject": "...",
  "email_body": "...",
  "linkedin_message": "...",
  "strengths": [
    "...",
    "...",
    "..."
  ]
}}

Contraintes :
- email_body : 60 à 100 mots
- commence par "Bonjour,"
- termine par "Cordialement, Lounis Arezki"
- linkedin_message : 25 à 50 mots
- strengths : exactement 3 éléments
"""

    last_error = None

    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini n'a retourné aucun texte"
                    )

                result = json.loads(response.text)

                required_fields = [
                    "subject",
                    "email_body",
                    "linkedin_message",
                    "strengths"
                ]

                for field in required_fields:
                    if field not in result:
                        raise ValueError(
                            f"Champ manquant : {field}"
                        )

                result["model_used"] = model

                return result

            except ServerError as e:
                last_error = e

                print(
                    f"⚠️ {model} indisponible, tentative {attempt + 1}/2"
                )

                time.sleep(3)

            except ClientError as e:
                last_error = e
                break

    raise RuntimeError(
        f"Aucun modèle Gemini disponible : {last_error}"
    )


def prepare_follow_up(profile, job, application):
    prompt = f"""
Tu rédiges une relance professionnelle pour une candidature de stage.

RÈGLE ABSOLUE :
N'invente aucune information.

CANDIDAT :
- Nom : {profile.get("name")}
- Bachelor 2 Informatique à EPITECH
- Recherche un stage développeur web / full-stack
- Début souhaité : {profile.get("start_date")}
- Durée : 4 à 6 mois

OFFRE :
- Entreprise : {job.get("company")}
- Poste : {job.get("title")}
- Lieu : {job.get("location")}

CANDIDATURE DÉJÀ ENVOYÉE :
Objet :
{application.get("subject", "")}

Email :
{application.get("email_body", "")}

OBJECTIF :
Faire une relance courte et polie après l'envoi de la candidature.

INTERDIT :
- inventer une réponse du recruteur
- dire qu'un entretien a déjà eu lieu
- inventer une expérience
- mettre de pression au recruteur
- utiliser un ton insistant

Retourne uniquement ce JSON :

{{
  "subject": "...",
  "follow_up_message": "...",
  "linkedin_message": "..."
}}

Contraintes :
- français
- message email entre 55 et 90 mots
- commence par "Bonjour,"
- rappelle brièvement la candidature
- montre toujours l'intérêt pour le poste
- termine par "Cordialement, Lounis Arezki"
- message LinkedIn entre 25 et 45 mots
"""

    last_error = None

    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini n'a retourné aucun texte"
                    )

                result = json.loads(response.text)

                required = [
                    "subject",
                    "follow_up_message",
                    "linkedin_message",
                ]

                for field in required:
                    if field not in result:
                        raise ValueError(
                            f"Champ manquant : {field}"
                        )

                result["model_used"] = model

                return result

            except ServerError as e:
                last_error = e
                time.sleep(3)

            except ClientError as e:
                last_error = e
                break

    raise RuntimeError(
        f"Aucun modèle Gemini disponible : {last_error}"
    )
