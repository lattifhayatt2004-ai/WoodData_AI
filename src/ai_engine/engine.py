# src/ai_engine/engine.py
from pydantic import ValidationError
from .config import client, SYSTEM_INSTRUCTION
from .validator import WoodDataResponse
import json
import streamlit as st
import sqlite3

def extract_wood_data(user_input: str) -> WoodDataResponse:
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=user_input,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "response_schema": WoodDataResponse.model_json_schema(),
        },
    )

    text = getattr(response, "text", None)
    if not text:
        raise ValueError("L'IA n'a produit aucun texte.")

    import re
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    if not cleaned.startswith("{"):
        raise ValueError("Réponse IA inattendue : format non JSON.")

    try:
        raw_dict = json.loads(cleaned)

        validated_data = WoodDataResponse.model_validate(raw_dict)
        return validated_data

    except json.JSONDecodeError:
        raise ValueError("Le format renvoyé par l'IA n'est pas un JSON valide.")

    except ValidationError as e:
        raise ValueError(
            f"Données non conformes au standard WoodData : {e.errors()}"
        )
        
@st.cache_data(show_spinner="Analyse WoodData en cours...", ttl=3600)
def extract_wood_data_cached(user_input: str):
    #Appelle ma fonction de validation crée précédement
    return extract_wood_data(user_input)

def log_action(user_id:int, action: str, details: dict):
    """Enregistre une trace indélébile dans la base SQLite"""
    conn = sqlite3.connect("wooddata.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute(
    "INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)",
        (user_id, action, json.dumps(details))
    )
    conn.commit()
    conn.close()
    
def extract_and_log(current_user_id: int, user_input: str):
    try:
        data = extract_wood_data_cached(user_input)

        # Log success (robuste)
        log_action(
            current_user_id,
            "IA_EXTRACTION_SUCCESS",
            {"client": data.client.model_dump() if hasattr(data.client, "model_dump") else data.client}
        )
        return data

    except Exception as e:
        log_action(current_user_id, "IA_EXTRACTION_FAILURE", {"error": str(e)})
        raise