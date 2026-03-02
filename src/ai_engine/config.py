from google import genai
import streamlit as st

# 1. Connexion sécurisée avec le nouveau SDK (2026)
# On utilise toujours ta clé stockée dans .streamlit/secrets.toml
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 2. Le Cerveau de WoodData AI (System Instruction)
# Ce bloc définit les règles métier pour RM LUXE BOIS
SYSTEM_INSTRUCTION = """
Tu es l'expert technique de WoodData AI pour l'entreprise RM LUXE BOIS.
Ton rôle est de transformer des notes de chantier brutes en données structurées (JSON).

RÈGLES D'EXTRACTION :
1. 'designation' : UN SEUL TEXTE formaté avec le NOM en gras.
   - Format : "**NOM** Descriptif technique complet".
   - Exemple : "**Porte** chêne épaisseur 5 cm contreplaqué double".
2. 'quantite' : Le nombre d'unités (Par défaut : 1).
3. 'ml' : Le métrage linéaire unitaire en mètres (si précisé, sinon null).
4. 'pu_ht' : Le prix unitaire hors taxe (sans la TVA de 20%).

LOGIQUE MÉTIER :
- Identifie les clients comme AKDITAL ou KG DESIGN.
- Ne jamais inventer de données. Si une info manque, utilise null.
- Sortie : JSON uniquement.
"""

# 3. Configuration de génération (Stabilité & Rigueur)
# On garde une température basse pour éviter les erreurs de calcul
generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 40,
    "response_mime_type": "application/json" # Formatage JSON strict
}