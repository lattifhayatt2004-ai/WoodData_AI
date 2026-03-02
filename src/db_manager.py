import sqlite3
import os
import hashlib
from datetime import datetime

# Chemins absolus pour éviter les erreurs de dossier
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'wooddata.db')
SQL_INIT_FILE = os.path.join(BASE_DIR, 'database', 'init_db.sql')

def hash_password(password):
    """Hash le mote de passe pour ne jamais le stocker en claie"""
    return hashlib.sha256(password.encode()).hexdigest()

def enregistrer_log(id_user, action, table_nom, id_enregistrement, details):
    """Enregistre chaque action dans la table audit_logs pour la traçabilité """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = """INSERT INTO audit_logs(id_user, action, table_nom,id_enregistrement, details ) VALUES(?, ?, ?, ?, ?)"""
        cursor.execute(query, (id_user, action, table_nom, id_enregistrement, details))
        conn.commit()
    except Exception as e:
        print(f"Erreur Audit Log : {e}")
    finally:
        conn.close()

def creer_utilisateur(email, password, role='EMPLOYE', nom=""):
    """
    Permet à l'Admin de créer des accès
    """
    pwd_hash = hash_password(password)
    try:
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        query="INSERT INTO users(email, password_hash, role, nom_utilisateur) VALUES(?,?,?,?)" 
        cursor.execute(query, (email, pwd_hash, role, nom))
        conn.commit()
        print(f"✅ Utilisateur {email} créé avec succès.")
    except sqlite3.IntegrityError:
        print(f"❌ ERREUR : L'email {email} est déjà utilisé.")
    finally:
        conn.close()
        
def verifier_connexion(email, password):
    """
    Vérifie les identifiants et retourne les infos utilisateur.
    """
    pwd_hash = hash_password(password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id_user, role, nom_utilisateur FROM users WHERE email=? AND password_hash=?", (email, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    return user  # Retourne None si échec, sinon (id_user, role, nom_utilisateur)

def obtenir_reliquat_projet(id_project):
    """
    Calcule le reste à facturer pour un projet donné.
    Combine les données de 'projects' et la somme de 'invoices'.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Obtenir le total TTC du devis [cite: 48]
        cursor.execute("SELECT total_ttc FROM projects WHERE id_project = ?", (id_project,))
        total_devis = cursor.fetchone()[0] or 0.0
        
        # 2. Obtenir le total déjà facturé [cite: 51]
        cursor.execute("SELECT SUM(montant_ttc) FROM invoices WHERE id_project = ?", (id_project,))
        total_facture = cursor.fetchone()[0] or 0.0
        
        return total_devis - total_facture
    except Exception as e:
        print(f"Erreur calcul reliquat : {e}")
        return 0.0
    finally:
        conn.close()

def init_database():
    """
    Initialise la base de données SQLite en utilisant le fichier init_db.sql.
    Crée les tables nécessaires pour WoodData AI (Clients, Projets, Users, Logs).
    """
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
        query = "SELECT SUM(montant_ttc) FROM invoices WHERE id_devis=?"
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