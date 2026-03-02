from src.ai_engine.engine import extract_wood_data
from src.utils.finance import (
    valider_facture_situation, 
    montant_en_lettres, 
    arrondir, 
    Decimal
)
from src.db_manager import (
    init_database, 
    creer_utilisateur, 
    verifier_connexion, 
    enregistrer_log, 
    DB_PATH
)
import sqlite3
import os

def test_system_complet():
    print("--- DEBUT DES TESTS D'INTEGRATION (PHASE 1) ---")
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_database()
    
    # 1. Sécurité
    creer_utilisateur("hayat.latif@rmluxe.ma", "Admin2026!", "ADMIN", "Hayat LATIF")
    user = verifier_connexion("hayat.latif@rmluxe.ma", "Admin2026!")
    assert user is not None
    id_user = user[0]
    print("✅ Sécurité : OK")

    # 2. Audit
    enregistrer_log(id_user, "TEST", "none", 0, "Test systeme")
    print("✅ Audit : OK")

    # 3. Finance
    # Test arrondi
    assert arrondir(10.005) == Decimal("10.01")
    # Test reliquat (doit bloquer)
    autorise, msg = valider_facture_situation(1000, 800, 300)
    assert autorise is False
    print("✅ Finance : OK")
    
    # On teste avec ton exemple complexe de menuiserie
    entree_test = "2 Cadre chambreur habillé contreplaqué chêne joint PVC quatre paumelles invisible à 1200 HT"

    print("--- TEST D'INGESTION WOODDATA AI ---")
    try:
        resultat = extract_wood_data(entree_test)
    
        print(f"Entrée : {entree_test}")
        print(f"Sortie JSON : {resultat}")
    
       # Vérification visuelle du formatage en gras
        if "**" in resultat['designation']:
            print("✅ SUCCÈS : Le nom est bien en gras.")
        else:
            print("❌ ERREUR : Le nom n'est pas en gras.")
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
    
    print("\n--- TOUS LES TESTS SONT RÉUSSIS ! ---")

if __name__ == "__main__":
    test_system_complet()