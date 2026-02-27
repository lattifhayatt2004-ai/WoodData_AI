import sqlite3
import os

# Chemins absolus pour éviter les erreurs de dossier
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'wooddata.db')
SQL_INIT_FILE = os.path.join(BASE_DIR, 'database', 'init_db.sql')

def init_database():
    # 1. Vérifier si le fichier SQL existe
    if not os.path.exists(SQL_INIT_FILE):
        print(f"ERREUR : Le fichier {SQL_INIT_FILE} est introuvable !")
        return

    # 2. Lire le contenu et vérifier s'il est vide
    with open(SQL_INIT_FILE, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    if not sql_script.strip():
        print(f"ERREUR : Le fichier {SQL_INIT_FILE} est vide !")
        return

    # 3. Créer le dossier database s'il n'existe pas
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # 4. Connexion et exécution
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(sql_script)
        conn.commit()
        
        # Vérification immédiate
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Succès ! Tables créées : {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"Erreur SQL : {e}")
    finally:
        conn.close()
        
def obtenir_total_facture(devis_id) :
    """
    Récupère la somme des montants TTC déjà facturés pour un devis donné
    """
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        #Somme des factures pour ce devis spécifique
        query = "SELECT SUM(montant_ttc) FROM Factures WHERE id_devis=devis_id "
        cursor.execute(query, (devis_id,))
        result = cursor.fetchone()[0]
        return float(result) if result else 0.0
    except Exception as e:
        print(f"Erreur lors de la lecture des factures : {e}")
        return 0.0
    finally:
        conn.close()
        
def obtenir_montant_devis(devis_id):
    """
    Récupère le montant total (Chiffre d'Affaires) prévu dans le devis initial[cite: 119].
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT chiffre_affaires_total FROM Devis WHERE id_devis = devis_id"
        cursor.execute(query, (devis_id,))
        
        resultat = cursor.fetchone()
        return float(resultat[0]) if resultat else 0.0
    except Exception as e:
        print(f"Erreur lors de la lecture du devis : {e}")
        return 0.0
    finally:
        conn.close()
    

if __name__ == "__main__":
    init_database()