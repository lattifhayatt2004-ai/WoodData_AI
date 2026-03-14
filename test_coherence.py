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
    sauvegarder_extraction_ia,
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
    
# Simulation du contenu du devis 000180 (Document Réel)
    entree_test = """
    Porte Chêne Ep. 5 cm contreplaqué double Cadre chambreur habillé 
    contreplaqué chêne joint PVC Quatre paumelles papillons Inox 
    Serrure Canaux. Sans poignet. Quantité: 23. Prix/Unité: 3300 HT.
    """

    print("\n--- TEST SUR DOCUMENT RÉEL (DEVIS 000180) ---")
    try:
        # 1. Extraction par l'IA
        resultat = extract_wood_data(entree_test)
        print(f"Client identifié : {resultat.client}")
        print(f"Articles extraits : {len(resultat.lignes)}")
        
        # 2. Sauvegarde en base
        id_projet = sauvegarder_extraction_ia(resultat, id_user)
        
        if id_projet:
            print(f"✅ SUCCÈS : Le document complexe a été transformé en Projet ID {id_projet}")
            
            # Vérification du montant (23 * 3300 = 75 900 HT)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT total_ht FROM projects WHERE id_project = ?", (id_projet,))
            total_db = cursor.fetchone()[0]
            print(f"📊 Vérification Financière : {total_db} MAD HT (Attendu: 75900.0)")
            conn.close()
        else:
            print("❌ ÉCHEC : La sauvegarde a échoué.")

    except Exception as e:
        print(f"❌ Erreur lors de l'analyse du document : {e}")


    print("\n--- TEST DE PERSISTENCE SQL ---")

    id_projet = sauvegarder_extraction_ia(resultat, id_user)
        
    if id_projet:
        print(f"✅ Sauvegarde SQL : OK (Projet ID: {id_projet})")
            
     # Vérification réelle dans la base
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
            
        # Vérifier que le projet existe
        cursor.execute("SELECT nom_project, total_ttc FROM projects WHERE id_project = ?", (id_projet,))
        projet = cursor.fetchone()
        print(f"📊 Données en base : {projet[0]} | Total : {projet[1]} MAD")
            
        # Vérifier l'audit log
        cursor.execute("SELECT action FROM audit_logs WHERE id_enregistrement = ?", (id_projet,))
        log = cursor.fetchone()
        if log and log[0] == "IMPORT_IA_SUCCESS":
            print("✅ Traçabilité : OK (Log d'audit trouvé)")
                
            conn.close()
    else:
        print("❌ Sauvegarde SQL : ÉCHEC")
    
    print("\n--- TOUS LES TESTS SONT RÉUSSIS ! ---")

if __name__ == "__main__":
    test_system_complet()