# src/ai_engine/engine.py
from pydantic import ValidationError
import re
from google import genai
from .config import client, SYSTEM_INSTRUCTION
from .validator import WoodDataResponse, WoodDataInvoiceResponse
import json
import streamlit as st
import sqlite3
import os

# Force le chemin absolu pour éviter le "no such table"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'database', 'wooddata.db')

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

def log_action(user_id: int, action: str, details: dict):
    """Enregistre une trace dans la base RM LUXE BOIS avec le bon chemin."""
    # Vérification de sécurité pour le développeur
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"La base de données est introuvable au chemin : {DB_PATH}")

    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    try:
        # Correction du nom de colonne : 'action' au lieu de 'action_type' [cite: 70]
        cursor.execute(
            "INSERT INTO audit_logs (id_user, action, details) VALUES (?, ?, ?)",
            (user_id, action, json.dumps(details))
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Erreur SQL : {e}")
        raise e
    finally:
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
    
def extract_invoice_data(prompt_enrichi: str) -> WoodDataInvoiceResponse:
    """
    Analyse les notes et le contexte pour générer une proposition de facture
    """
    reponse = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt_enrichi,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "response_schema": WoodDataInvoiceResponse.model_json_schema(),
        },
    )
    
    try:
        #Nettoyage et validation
        cleaned =re.sub(r"^```json\s*", "", reponse.text.strip())
        return WoodDataInvoiceResponse.model_validate(json.loads(cleaned))
    except Exception as e:
        raise ValueError(f"Erreur d'analyse comptable IA : {e}")
    