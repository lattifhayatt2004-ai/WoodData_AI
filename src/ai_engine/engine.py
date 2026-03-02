# src/ai_engine/engine.py
from .config import client, SYSTEM_INSTRUCTION
import json

def extract_wood_data(user_input: str) -> dict:
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=user_input,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    )

    # 1) Si le SDK a parsé automatiquement, on prend ça
    if getattr(response, "parsed", None) is not None:
        return response.parsed

    # 2) Sinon on récupère le texte brut
    text = getattr(response, "text", None)
    if not text:
        # cas: réponse vide / bloquée / format inattendu
        raise ValueError(f"Réponse Gemini vide ou non lisible. Response={response}")

    # 3) Nettoyage si jamais le modèle met des fences ```json
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    # 4) Parsing JSON
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini n'a pas renvoyé un JSON valide.\nTexte reçu:\n{text}") from e