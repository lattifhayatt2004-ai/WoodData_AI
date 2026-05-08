import sqlite3
import os
import hashlib
from datetime import datetime
from decimal import Decimal
import pandas as pd
from src.utils.finance import (
    calculer_bilan_devis,
    calculer_ecart_financier,
    generer_plan_ventilation)

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
        

def sauvegarder_extraction_ia(data, user_id):
    """
    Transforme le JSON de Gemini en Client, Projet et Articles en base.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Gérer le Client (On le crée s'il n'existe pas)
        cursor.execute("SELECT id_client FROM clients WHERE nom_client = ?", (data.client,))
        res = cursor.fetchone()
        if res:
            id_client = res[0]
        else:
            cursor.execute("INSERT INTO clients (nom_client) VALUES (?)", (data.client,))
            id_client = cursor.lastrowid

        # 2. Calculer les totaux financiers du projet via ton moteur finance.py
        # On convertit les Decimal en float pour SQLite
        lignes_ht = [Decimal(str(item.pu_ht)) * Decimal(str(item.quantite or 1)) for item in data.lignes]
        bilan = calculer_bilan_devis(lignes_ht)

        # 3. Créer le Projet (table projects)
        cursor.execute("""
            INSERT INTO projects (id_client, nom_project, total_ht, total_ttc)
            VALUES (?, ?, ?, ?)
        """, (id_client, f"Dossier {data.client}", float(bilan['total_ht']), float(bilan['total_ttc'])))
        id_project = cursor.lastrowid

        # 4. Insérer chaque article (table project_items)
        for item in data.lignes:
            cursor.execute("""
                INSERT INTO project_items (id_project, designation, quantite, metrage, pu_ht)
                VALUES (?, ?, ?, ?, ?)
            """, (id_project, item.designation, item.quantite, item.ml, float(item.pu_ht)))

        conn.commit()
        
        # 5. Tracer l'action dans l'audit log
        enregistrer_log(user_id, "IMPORT_IA_SUCCESS", "projects", id_project, f"Client: {data.client}")
        
        return id_project

    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la sauvegarde IA : {e}")
        return None
    finally:
        conn.close()
        
def obtenir_statistiques_globales():
    """
    Calcule les indicateurs clés pour le Dashboard Admin :
    CA Total, Total Encaissé, et Reste à Percevoir."""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        #1. Somme de tous les devis (Chiffre d'Affaires Total)
        cursor.execute("SELECT SUM(total_ttc) FROM estimates WHERE est_valide = 1")
        ca_total = cursor.fetchone()[0] or 0.0
        
        #2. Somme de tous les paiements (Trésorerie réelle)
        cursor.execute("SELECT SUM(montant_mad) FROM payments")
        total_encaisse = cursor.fetchone()[0] or 0.0
        
        #3. Reste à percevoir = CA Total - Total Encaissé
        reste_a_percevoir = ca_total - total_encaisse
        
        return {
            "ca_total": ca_total,
            "total_encaisse": total_encaisse,
            "reste_a_percevoir": reste_a_percevoir
        }
    except Exception as e:
        print(f"Erreur stats :{e}")
        return {
            "ca_total": 0.0,
            "total_encaisse": 0.0,
            "reste_a_percevoir": 0.0
        }
    finally:
        conn.close()
        
def obtenir_liste_projets_complet():
    """
    Retourne la liste des projets avec le nom du client pour le Dashboard"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
        SELECT p.id_project, p.nom_project, c.nom_client, e.total_ttc, p.date_creation
        FROM projects p
        JOIN  estimates e ON p.id_project = e.id_project AND e.est_valide = 1
        JOIN clients c ON p.id_client = c.id_client
        ORDER BY p.date_creation DESC
        """
    cursor.execute(query)
    projets = cursor.fetchall()
    conn.close()
    return projets

def obtenir_projets_a_facturer():
    """
    Récupère les projets dont le montant TTC est supérieur au total déjà facturé
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()   
        
        # Jointure entre projets et invoices pour calculer le reste
        query = """
            SELECT p.id_project, p.nom_project, p.total_ttc,
                   COALESCE(SUM(i.montant_ttc),0) as deja_facture
            FROM projects p
            LEFT JOIN invoices i ON p.id_project = i.id_project
            GROUP BY p.id_project
            HAVING deja_facture < p.total_ttc
            """
        
        cursor.execute(query)
        projets = cursor.fetchall()
        return projets
    except Exception as e:
        print(f"Erreur projets à facturer : {e}")
        return []
    finally:
        conn.close()

def sauvegarder_facture_pre_ventilee(id_project, num_facture, montant_total, liste_ventilation, id_user):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 1. Création de l'entête de facture
        cursor.execute(
            "INSERT INTO invoices (id_project, num_facture, montant_ttc) VALUES (?, ?, ?)",
            (id_project, num_facture, float(montant_total))
        )
        id_invoice = cursor.lastrowid #

        # 2. Insertion précise des lignes (La cascade validée)
        for ligne in liste_ventilation:
            cursor.execute(
                "INSERT INTO invoice_line_details (id_invoice, id_project_item, montant_alloue) VALUES (?, ?, ?)",
                (id_invoice, ligne['id_item'], float(ligne['montant_pris']))
            ) # 

        # 3. Mise à jour de l'audit
        enregistrer_log(id_user, "CREATE_INVOICE_VENTILEE", "invoices", id_invoice, f"Facture {num_facture} ventilée")
        
        conn.commit()
        return True, "Facture enregistrée avec succès."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
        
def supprimer_utilisateur(email):
    """
    Supprime un utilisateur de la base de données via son email.
    Assure la gestion de la sécurité du personnel[cite: 63, 65].
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Suppression sécurisée
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        return True, f"L'utilisateur {email} a été supprimé avec succès."
    except Exception as e:
        print(f"Erreur lors de la suppression : {e}")
        return False, str(e)
    finally:
        conn.close()
        
def enregistrer_paiement(id_project, montant_mad, mode_paiement, date_paiement, id_user):
    """
    Enregistre un règlement client (Chèque, Virement, Espèces).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Insertion du paiement
        query = """INSERT INTO payments (id_project, montant_mad, mode_paiement, date_paiement) 
                   VALUES (?, ?, ?, ?)"""
        cursor.execute(query, (id_project, montant_mad, mode_paiement, date_paiement))
        id_paiement = cursor.lastrowid
        
        # 2. Audit Log pour la traçabilité exigée
        enregistrer_log(id_user, 'ADD_PAYMENT', 'payments', id_paiement, f"Montant: {montant_mad} MAD | Mode: {mode_paiement}")
        
        conn.commit()
        return True, "Paiement enregistré avec succès."
    except Exception as e:
        return False, f"Erreur : {e}"
    finally:
        conn.close()
        
def obtenir_reste_a_facturer(id_project):
    """Calcule le reste à encaisser réel (Total Devis - Total Paiements)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # 1. Total du Devis 1 
        cursor.execute("SELECT total_ttc FROM estimates WHERE est_valide = 1 AND id_project = ?", (id_project,))
        res_devis = cursor.fetchone()
        total_devis = res_devis[0] if res_devis else 0.0
        
        # 2. Total déjà payé
        cursor.execute("SELECT SUM(montant_mad) FROM payments WHERE id_project = ?", (id_project,))
        res_paye = cursor.fetchone()
        total_paye = res_paye[0] if res_paye and res_paye[0] else 0.0
        
        return total_devis - total_paye
    except Exception:
        return 0.0
    finally:
        conn.close()
        
def ventiler_montant_sur_articles(id_project, id_invoice, montant_facture_ttc):
    """
    Répartit le montant d'une facture sur les articles du projet au prorata.
    Consomme les articles dans l'ordre jusqu'à épuisement du montant de la facture.
    """
    
    contexte = obtenir_contexte_facturation(id_project)
    plan = generer_plan_ventilation(montant_facture_ttc, contexte['articles_disponibles'])
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for ligne in plan:
            cursor.execute("""
                INSERT INTO invoice_line_details (id_invoice, id_project_item, montant_alloue)
                VALUES (?, ?, ?)
            """, (id_invoice, ligne['id_item'], ligne['montant_pris']))
        conn.commit()
        return True
    finally:
        conn.close()
        
def valider_devis_final(id_project, id_estimate_a_valider, id_user) :
    """
    Définit un devis spécifique comme étant la référance contractuelle du projet.
    """
    try :
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. On annule toute validation précédente pour ce projet
        cursor.execute("UPDATE estimates SET est_valide = 0 WHERE id_project = ?", (id_project,))
        
        # 2. Marquer le devis sélectionné comme valide
        cursor.execute("UPDATE estimates SET est_valide = 1 WHERE id_estimate = ?", (id_estimate_a_valider,))
        
        # 3. Audit Log pour la traçabilité
        cursor.execute("UPDATE projects SET statut_projet = 'Validé / En Cours' WHERE id_project = ?", (id_project,))
        conn.commit()
        
        # 4. Audit Log pour la traçabilité
        enregistrer_log(id_user, "VALIDATE_ESTIMATE", "estimates", id_estimate_a_valider, f"Projet {id_project} validé")
        return True, "Devis validé avec succès !"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
        
def obtenir_contexte_facturation(id_project):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    #1. Infos Client (Entreprise vs particulier)
    cursor.execute("""
            SELECT c.id_client, c.nom_client, c.ice_client, p.nom_projet
            FROM projects p 
            JOIN clients c ON p.id_client = c.id_client
            WHERE p.id_project = ?
        """, (id_project,))
    client_info = cursor.fetchone()    
        
    #2. Dérnière série facture 
    cursor.execute("SELECT num_facture FROM invoices ORDER BY id_invoice DESC LIMIT 1")
    derniere_serie = cursor.fetchone()
        
    #3. Etat des articles 
    # On calcule : Prix Total - Somme des montants déjà alloués dans invoice_line_details
    cursor.execute("""
        SELECT pi.id_item, pi.designation, (pi.quantite * pi.pu_ht) as total_article,
                   IFNULL(SUM(ild.montant_alloue), 0) as deja_facture
        FROM project_items pi
        JOIN estimates e ON pi.id_estimate = e.id_estimate
        LEFT JOIN invoice_line_details ild ON pi.id_item = ild.id_project_item
        WHERE e.id_project = ? AND e.est_valide = 1
        GROUP BY pi.id_item
        """, (id_project,))
    articles = cursor.fetchall()
    
    conn.close() 
        
    return {
        "client": {"id": client_info[0], "nom": client_info[1], "ice": client_info[2]},
        "projet_nom": client_info[3],
        "serie_actuelle": derniere_serie[0] if derniere_serie else "Facture-Client-000",
        "articles_disponibles": [
            {"id": a[0], "nom": a[1], "reste": a[2] - a[3]} for a in articles if (a[2] - a[3]) > 0
        ]
    }

def obtenir_liste_clients():
    """
    Récupère tous les clients de la base de données pour les menus Streamlit.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Utiliser Row permet d'accéder aux colonnes par leur nom
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_client, nom_client, ice_client FROM clients ORDER BY nom_client")
        rows = cursor.fetchall()
        
        # On transforme le résultat en une liste de dictionnaires propre
        clients = [dict(row) for row in rows]
        conn.close()
        return clients
    except Exception as e:
        print(f"Erreur lors de la récupération des clients : {e}")
        return []
    
def ajouter_projet_express(id_client, nom_project, description="Projet manuel sans devis"):
    """
    Crée un projet directement en base de données pour les interventions rapides.
    Retourne l'ID du projet créé ou (False, erreur).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # On insère le projet avec le strict minimum
        # id_user peut être récupéré via la session Streamlit plus tard
        query = """
            INSERT INTO projects (id_client, nom_project, date_creation, statut_projet) 
            VALUES (?, ?, CURRENT_DATE, 'En cours')
        """
        cursor.execute(query, (id_client, nom_project))
        id_nouveau_projet = cursor.lastrowid
        
        conn.commit()
        return id_nouveau_projet, "Projet créé avec succès."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
        
def sauvegarder_facture_projet_manuel(id_project, num_facture, montant_ttc, id_user) :
    """
    Lie directement une facture à un projet manuel sans passer par un devis.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        #1. On crée l'entête de la facture
        cursor.execute(
            "INSERT INTO invoices (id_project, num_facture, montant_ttc) VALUES(?,?,?)",
            (id_project, num_facture, float(montant_ttc))
        )
        id_invoice = cursor.lastrowid
        
        #2. On crée une ligne de détail générique liée au projet (mais sans article de devis)
        cursor.execute(
            "INSERT INTO invoice_line_details (id_invoice, id_project_item, montant_alloue) VALUES (?, NULL, ?)",
            (id_invoice, float(montant_ttc))
        )
        
        # 3. On trace l'opération
        enregistrer_log(id_user, "MANUAL_PROJECT_INVOICE", "invoices", id_invoice, f"Facture directe projet {id_project}")
        
        conn.commit()
        return True, "Facture liée au projet avec succès."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
        
def obtenir_situation_projets_client(id_client):
    conn = sqlite3.connect(DB_PATH)
    # On utilise LEFT JOIN pour ne perdre aucun projet, même ceux sans facture
    query = """
        SELECT 
            p.id_project,
            p.nom_project,
            p.date_creation,
            COALESCE(SUM(i.montant_ttc), 0) as total_facture,
            COALESCE((SELECT SUM(py.montant_mad) FROM payments py 
                      JOIN invoices inv ON py.id_invoice = inv.id_invoice 
                      WHERE inv.id_project = p.id_project), 0) as total_paye
        FROM projects p
        LEFT JOIN invoices i ON p.id_project = i.id_project
        WHERE p.id_client = ?
        GROUP BY p.id_project
    """
    df = pd.read_sql_query(query, conn, params=(id_client,))
    df['reste_a_percevoir'] = df['total_facture'] - df['total_paye']
    conn.close()
    return

def ajouter_nouveau_client(nom, ice="", num_tel="") :
    """Crée un nouveau client pour RM LUXE CLIENT"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clients (nom_client, ice_client, telephone_client) VALUES (?, ?, ?)", (nom, ice, num_tel))
        conn.commit()
        return True, "Client ajouté avec succès."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def supprimer_client_db(id_client):
    """Supprime un client (Attention: possible si aucun projet n'est lié)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérification de l'absence de projets liés
        cursor.execute("SELECT COUNT(*) FROM projects WHERE id_client = ?", (id_client,))
        if cursor.fetchone()[0] > 0:
            return False, "Impossible de supprimer ce client car des projets y sont liés."
        
        cursor.execute("DELETE FROM clients WHERE id_client = ?", (id_client,))
        conn.commit()
        return True, "Client supprimé avec succès."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
        
def obtenir_bilan_financier(id_cible, type_cible="projet"):
    """
    Calculate le bilan selonl'ID du projet ou l'ID du client.
    type_cible : "projet" ou "client"
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if type_cible == "projet":
            # Somme des factures du projet (IA ou manuel)
            cursor.execute("SELECT SUM(montant_ttc) FROM invoices WHERE id_project = ?", (id_cible,))
            total_facture = cursor.fetchone()[0] or 0.0
            
            # Somme des paiements pour ce projet[cite: 1]
            cursor.execute("SELECT SUM(montant_mad) FROM payments WHERE id_project = ?", (id_cible,))
            total_paye = cursor.fetchone()[0] or 0.0
        else:
            # Somme de toutes les factures de tous les projets d'un client[cite: 1]
            cursor.execute("""
                SELECT SUM(i.montant_ttc) FROM invoices i
                JOIN projects p ON i.id_project = p.id_project
                WHERE p.id_client = ?""", (id_cible,))
            total_facture = cursor.fetchone()[0] or 0.0
            
            # Somme de tous les paiements du client[cite: 1]
            cursor.execute("SELECT SUM(montant_mad) FROM payments WHERE id_project IN (SELECT id_project FROM projects WHERE id_client = ?)", (id_cible,))
            total_paye = cursor.fetchone()[0] or 0.0
            
        return {
            "total_facture": total_facture,
            "total_paye": total_paye,
            "reste": float(calculer_ecart_financier(total_facture, total_paye))
        }
        
    except Exception as e:
        print(f"Erreur bilan : {e}")
        return {"total_facture": 0, "total_paye": 0, "reste": 0}
    
    finally:
        conn.close()
    
def changer_statut_projet(id_project, nouveau_statut, id_user):
    """
    Met à jour le statut du projet (En cours, Terminé, Annulé).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Mise à jour du statut
        cursor.execute(
            "UPDATE projects SET statut_projet = ? WHERE id_project = ?",
            (nouveau_statut, id_project)
        )
        
        # 2. Audit Log pour savoir qui a fermé le dossier
        enregistrer_log(id_user, f"STATUS_CHANGE_{nouveau_statut.upper()}", "projects", id_project, f"Statut passé à {nouveau_statut}")
        
        conn.commit()
        return True, f"Le projet est désormais : {nouveau_statut}"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
        
def modifier_montant_facture_manuelle(id_invoice, nouveau_montant, id_user):
    """
    Modifie le montant d'une facture et enregistre l'ancien montant dans l'audit log.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Récupérer l'ancien montant et le numéro de facture pour le log
        cursor.execute("SELECT montant_ttc, num_facture FROM invoices WHERE id_invoice = ?", (id_invoice,))
        ancienne_data = cursor.fetchone()
        
        if not ancienne_data:
            return False, "Facture introuvable."
        
        ancien_montant = ancienne_data[0]
        num_facture = ancienne_data[1]

        # 2. Mise à jour du montant dans la table invoices
        cursor.execute("UPDATE invoices SET montant_ttc = ? WHERE id_invoice = ?", (nouveau_montant, id_invoice))
        
        # 3. Mise à jour de la ventilation (on ajuste la ligne de détail)
        # On cible la ligne qui n'est pas liée à un article spécifique (cas manuel)
        cursor.execute("""
            UPDATE invoice_line_details 
            SET montant_alloue = ? 
            WHERE id_invoice = ? AND id_project_item IS NULL
        """, (nouveau_montant, id_invoice))

        # 4. Enregistrement dans l'Audit Log (La trace sacrée)
        details_log = f"Facture {num_facture} : Ancien montant {ancien_montant} MAD -> Nouveau montant {nouveau_montant} MAD"
        enregistrer_log(id_user, 'UPDATE_INVOICE_AMOUNT', 'invoices', id_invoice, details_log)

        conn.commit()
        return True, f"La facture {num_facture} a été modifiée avec succès."
    except Exception as e:
        return False, f"Erreur lors de la modification : {str(e)}"
    finally:
        conn.close()
        
def obtenir_historique_logs():
    """
    Récupère tous les logs d'audit avec le nom de l'utilisateur associé.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT 
                l.date_action, 
                u.nom_utilisateur, 
                l.action, 
                l.table_nom, 
                l.details 
            FROM audit_logs l
            LEFT JOIN users u ON l.id_user = u.id_user
            ORDER BY l.date_action DESC
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Erreur lors de la récupération des logs : {e}")
        return pd.DataFrame()
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()