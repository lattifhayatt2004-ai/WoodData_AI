import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import json
from src.db_manager import (
    verifier_connexion, 
    obtenir_statistiques_globales, 
    obtenir_liste_projets_complet, 
    creer_utilisateur,
    supprimer_utilisateur,
    obtenir_liste_clients,
    enregistrer_log,
    sauvegarder_facture_pre_ventilee,
    sauvegarder_facture_projet_manuel,
    enregistrer_paiement,
    ajouter_projet_express,
    obtenir_reste_a_facturer,
    ajouter_nouveau_client,
    supprimer_client_db,
    obtenir_bilan_financier,
    changer_statut_projet,
    valider_devis_final,
    modifier_montant_facture_manuelle,
    obtenir_historique_logs,
    DB_PATH
)

# 1. Gestion des chemins
BASE_DIR = Path(__file__).resolve().parent
logo_path = BASE_DIR / "assets" / "Logo_RMLB.png"  # corrigé commentaire (PNG cohérent)

def inject_custom_style():
    st.markdown(
        """
        <style>
        .stApp { background-color: #073A2D; color: #FFFFFF; }
        [data-testid="stSidebar"] { background-color: #03251D; border-right: 2px solid #BF9B30; }
        input { color: #073A2D !important; }
        .stRadio > div { color: #BF9B30; }
        [data-testid="metric-container"] {
            background-color: #0B523F;
            border: 1px solid #BF9B30;
            padding: 20px;
            border-radius: 10px;
            color: #FFFFFF;
            box-shadow: 2px 2px 10px rgba(191, 155, 48, 0.2);
        }
        h1, h2, h3, h4, h5, h6 { color: #BF9B30 !important; }
        .stTextArea textarea { background-color: #0B523F; color: #FFFFFF; border: 1px solid #BF9B30; }
        .stButton>button { background-color: #BF9B30; color: #073A2D; border-radius: 5px; border: none; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True
    )

# 2. Configuration
st.set_page_config(page_title="WoodData AI - RM LUXE BOIS", layout="wide")
inject_custom_style()

# 3. Session
if 'auth_status' not in st.session_state:
    st.session_state.update({
        'auth_status': False,
        'user_id': None,
        'role': None,
        'user_nom': ""
    })

def login_page():
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.title("WoodData - AI")

        st.write("### Système de Gestion Intelligent")
        with st.form("login_form"):
            email = st.text_input("Email professionnel")
            password = st.text_input("Mot de passe", type="password")

            if st.form_submit_button("S'AUTHENTIFIER"):
                user = verifier_connexion(email, password)
                if user:
                    st.session_state['auth_status'] = True
                    st.session_state['user_id'] = user[0]
                    st.session_state['role'] = user[1]
                    st.session_state['user_nom'] = user[2]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

def main_app():
    # Sidebar
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=150)
    st.sidebar.title(f"👤 {st.session_state['user_nom']}")
    st.sidebar.write(f"Rôle : **{st.session_state['role']}**")

    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()  # amélioration sécurité
        st.rerun()

    # Menu
    if st.session_state.get('role') == 'ADMIN' :
        menu = ["Tableau de Bord", "Gestion des Projets", "Facturation & Paiements", "Suivi & Reporting", "Paramètres"]
    else:
        menu = ["Saisie Devis / Facture", "Projets en cours"]

    choice = st.sidebar.radio("Navigation", menu)

    # Tableau de bord
    if choice == "Tableau de Bord":
        st.header("📊 Résumé de l'Activité - RM LUXE BOIS")
        stats = obtenir_statistiques_globales()

        col1, col2, col3 = st.columns(3)
        col1.metric("Chiffre d'Affaires (TTC)", f"{stats['ca_total']:,} MAD")
        col2.metric("Total Encaissé", f"{stats['total_encaisse']:,} MAD")
        col3.metric("Reste à Percevoir", f"{stats['reste_a_percevoir']:,} MAD")

        st.divider()
        st.subheader("📋 Liste des Projets Récents")

        projets = obtenir_liste_projets_complet()
        if projets:
            df = pd.DataFrame(projets, columns=["ID", "Projet", "Client", "Montant TTC", "Date"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun projet en base de données.")

    elif choice == "Gestion des Projets":
        st.title("🏗️ Projets et Devis")
        
        #Menu de sélection du type de projet
        mode_projet = st.radio(
            "Type de création:",
            ["📄 Nouveau Devis (IA)", "⚡ Intervention Rapide (Manuel)", "🏁 Validation du Dossier"],
             horizontal=True
        )
        
        if mode_projet == "⚡ Intervention Rapide (Manuel)":
            st.subheader("Créer une intervention sans devis")
            
            #1. Récupération sécurisée de la liste
            liste_clients = obtenir_liste_clients()
            
            if not liste_clients :
                st.warning("⚠️ Aucun client trouvé. Veuillez d'abord ajouter un client dans la base de données.")
            
            else :
                
                options_clients = {c['nom_client']: c['id_client'] for c in liste_clients}
                noms_clients = ["-- Choisir un client --"] + list(options_clients.keys())
                nom_client_sel =st.selectbox("👤 Sélectionner le Client", noms_clients)
                
                if nom_client_sel != "-- Choisir un client --":
                    
                    id_client_sel = options_clients[nom_client_sel]
            
                    #2. Saisie des infos projet
                    nom_interv = st.text_input("🎯 Nom de l'intervention", placeholder="Ex: Modification portes placard")
                    desc_interv = st.text_area("📝 Description (Optionnel)", placeholder="Détails sur l'intervention...")
            
                    if st.button("🚀 Créer le Projet"):
                        if not nom_interv.strip():
                            st.warning("Veuillez donner un nom à l'intervention.")
                        else:
                            # Appel de la fonction "Projet Express" créée à l'étape 1
                            id_nouveau, msg = ajouter_projet_express(id_client_sel, nom_interv, desc_interv)
            
                            if id_nouveau:
                                st.success(f"✅ Projet '{nom_interv}' créé avec succès (ID: {id_nouveau})")
                                # On enregistre l'action dans l'audit pour la traçabilité
                                enregistrer_log(st.session_state['user_id'], "CREATE_PROJECT_MANUAL", "projects", id_nouveau, nom_interv)
                                st.balloons()
                            else:
                                st.error(f"Erreur lors de la création : {msg}")
            
        elif mode_projet == "📄 Nouveau Devis (IA)":
                with st.expander("➕ Ajouter un nouveau projet (IA WoodData)"):
                    user_input = st.text_area("Collez les notes de chantier ou le descriptif ici :")

                    if st.button("Lancer l'analyse IA"):
                        with st.spinner("Analyse en cours..."):
                            try:
                                from src.ai_engine.engine import extract_and_log
                                resultat = extract_and_log(st.session_state['user_id'], user_input)
                                st.success("Données extraites avec succès !")
                                st.data_editor(resultat.lignes)
                            except Exception as e:
                                st.error(f"Erreur : {e}")
        
        elif mode_projet == "🏁 Validation du Dossier":
            projets = obtenir_liste_projets_complet()
            if not projets:
                st.info("Aucun projet existant. Créez-en un d'abord.")
            # Option pour créer un projet ici si besoin
            else:
                # p[0] est id_project, p[1] est le nom, p[2] est le client
                options_p = {f"{p[1]} ({p[2]})": p[0] for p in projets}
                nom_projet_sel = st.selectbox("Sélectionner un projet à gérer", options_p.keys())
                id_proj = options_p[nom_projet_sel]
            
            # 1. On liste tous les devis associés au projet id_proj
                try:
                    conn = sqlite3.connect(DB_PATH)
                    # On récupère les versions de devis pour ce projet
                    query = "SELECT id_estimate, version_numero, total_ttc, est_valide FROM estimates WHERE id_project = ?"
                    df_devis = pd.read_sql_query(query, conn, params=(id_proj,))
                    conn.close()

                    if df_devis.empty:
                        st.warning("ℹ️ Aucun devis trouvé pour ce projet. Veuillez en générer un via l'IA.")
                    else:
                        # On crée une liste d'options pour le selectbox
                        options_devis = {
                            f"Devis v{row['version_numero']} - {row['total_ttc']:,.2f} MAD {'(VALIDÉ)' if row['est_valide'] else ''}": row['id_estimate']
                            for _, row in df_devis.iterrows()
                        }
        
                        devis_sel_nom = st.selectbox("Sélectionner le devis définitif :", options_devis.keys())
                        id_estimate_a_valider = options_devis[devis_sel_nom]

                        if st.button("✅ Confirmer ce devis comme Référence"):
                            # Appel de ta fonction backend existante
                            success, msg = valider_devis_final(id_proj, id_estimate_a_valider, st.session_state['user_id'])
                            if success:
                                st.success(f"Le projet est maintenant officiellement 'En Cours'.")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(msg)
                except Exception as e:
                    st.error(f"Erreur lors de la récupération des devis : {e}")

    elif choice == "Facturation & Paiements":
        st.title("💰 Flux Financiers")

        tous_les_projets = obtenir_liste_projets_complet()
        
        if not tous_les_projets:
            st.info("ℹ️ Aucun projet n'est enregistré en base pour le moment.")
            st.stop()  # correction crash id_proj
            
        if 'proposition_ia' not in st.session_state:
            st.session_state.proposition_ia = None
            
        noms_projets = {f"{p[1]} (Client: {p[2]})": p[0] for p in tous_les_projets}
        projet_nom = st.selectbox("🎯 Sélectionnez le projet à gérer", list(noms_projets.keys()))
        id_proj = noms_projets[projet_nom]

        tab1, tab2, tab3 = st.tabs(["➕ Ajouter une Facture", "💸 Enregistrer un Paiement", "🛠️ Correction de Facture Manuelle"])

        with tab1:
            st.subheader("Nouvelle facture de situation")
            reliquat = obtenir_bilan_financier(id_proj, 'projet')['total_facture']

            if reliquat <= 0:
                st.success("✅ Ce projet est déjà entièrement facturé.")
            else:
                st.warning(f"💰 Montant disponible : **{reliquat:,.2f} MAD**")
                
                instructions_pere = st.text_area(
                    "Instructions de facturation :",
                    placeholder="Ex Facturer 10 000 MAD pour l'avancement du chantier KG Design",
                    help="L'IA calculera automatiquement la série et la répartition sur les articles."
                )
                
                if st.button("🪄 Analyser et Préparer la Facture") :
                    if not instructions_pere.strip():
                        st.warning("Veuillez saisir une instruction.")
                    else :
                        with st.spinner("Calcul de la cascade en cours ..."):
                            #A. Récupération du contexte réel (via db_manager)
                            from src.db_manager import obtenir_contexte_facturation
                            contexte_reel = obtenir_contexte_facturation(id_proj)
                            
                            #B. Appel à l'IA (On injecte le JSON dans le prompt)
                            from src.ai_engine.engine import extract_invoice_data
                            prompt_final = f"CONTEXTE DB: {json.dumps(contexte_reel)}\n NOTE: {instructions_pere}"
                            st.session_state.proposition_ia = extract_invoice_data(prompt_final)
                            

                                # Bouton de confirmation finale
                            if st.session_state.proposition_ia:
                                prop = st.session_state.proposition_ia
                                st.info(f"### Proposition : {prop.num_facture_propose}")
                                st.write(f"**Montant Total :** {prop.montant_total_facture:,.2f} MAD")
        
                                df_v = pd.DataFrame(prop.ventilation)
                                st.table(df_v)
                                
                                if st.button("✅ Confirmer l'enregistrement final"):
                                    # On vérifie s'il y a des articles à ventiler ou si c'est une ligne vide
                                    if not prop.ventilation:
                                        # Cas Projet Manuel sans articles : on utilise la fonction dédiée
                                        success, msg = sauvegarder_facture_projet_manuel(
                                        id_proj, prop.num_facture_propose, prop.montant_total_facture, st.session_state['user_id']
                                        )
                                    else:
                                        # Cas avec articles : ventilation classique
                                        success, msg = sauvegarder_facture_pre_ventilee(
                                            id_proj, prop.num_facture_propose, prop.montant_total_facture, prop.ventilation, st.session_state['user_id']
                                        )
            
                                    if success:
                                        st.success("Enregistré en base de données !")
                                        st.session_state.proposition_ia = None # On vide après succès
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            
        with tab2:
            st.subheader("Encaissement libre")

            reliquat_fact = obtenir_bilan_financier(id_proj, 'projet')['total_facture']
            reste_a_encaisser = obtenir_reste_a_facturer(id_proj)

            col1, col2 = st.columns(2)
            col1.metric("Reste à Facturer", f"{reliquat_fact:,.2f} MAD")
            col2.metric("Solde Client", f"{reste_a_encaisser:,.2f} MAD")

            with st.form("form_paiement"):
                m_p = st.number_input("Montant", min_value=0.0)
                mode_p = st.selectbox("Mode", ["Virement", "Chèque", "Espèces"])

                if st.form_submit_button("Valider"):
                    if m_p <= 0:
                        st.error("Montant invalide")
                    else:
                        from datetime import datetime
                        success, msg = enregistrer_paiement(id_proj, m_p, mode_p, datetime.now().strftime('%Y-%m-%d'), st.session_state['user_id'])
                        if success:
                            st.success(msg)
                            st.rerun()
        with tab3:
            # On récupère les factures du projet sélectionné
            conn = sqlite3.connect(DB_PATH)
            df_inv = pd.read_sql_query("SELECT id_invoice, num_facture, montant_ttc FROM invoices WHERE id_project = ?", conn, params=(id_proj,))
            conn.close()

            if not df_inv.empty:
                # Création d'un dictionnaire pour le selectbox
                dict_inv = {f"Facture {row['num_facture']} ({row['montant_ttc']} MAD)": row['id_invoice'] for _, row in df_inv.iterrows()}
                inv_a_modifier = st.selectbox("Choisir la facture à corriger :", dict_inv.keys())
        
                nouveau_mt = st.number_input("Nouveau montant TTC (MAD) :", min_value=0.0, format="%.2f")
        
                if st.button("💾 Enregistrer la modification"):
                    if nouveau_mt > 0:
                        id_inv_sel = dict_inv[inv_a_modifier]
                        success, msg = modifier_montant_facture_manuelle(id_inv_sel, nouveau_mt, st.session_state['user_id'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Le montant doit être supérieur à 0.")   
                
    elif choice == "Suivi & Reporting":
        st.header("📈 Analyse de l'Avancement des Paiements")

        # 1. Choix du mode de vue
        mode_vue = st.radio("Analyser par :", ["👤 Client (Dette Globale)", "🎯 Projet (Détail Caisse)"], horizontal=True)
        id_cible = None
        type_cible = "projet"
        
        if mode_vue == "👤 Client (Dette Globale)":
            # Utilise ta fonction existante pour la liste)
            clients = obtenir_liste_clients()
            if clients:
                options_c = {c['nom_client']: c['id_client'] for c in clients}
                nom_c = st.selectbox("Sélectionner le client :", options_c.keys())
                id_cible = options_c[nom_c]
                type_cible = "client"
            else:
                st.info("Aucun client en base.")
                st.stop()
            
        else:
            # Utilise ta fonction existante pour les projets
            projets = obtenir_liste_projets_complet()
            if projets:
                options_p = {f"{p[1]} ({p[2]})": p[0] for p in projets}
                nom_p = st.selectbox("Sélectionner le projet :", options_p.keys())
                id_cible = options_p[nom_p]
                type_cible = "projet"
            else:
                st.info("Aucun projet en base.")
                st.stop()
        
        # 2. Calculs et affiche des metrics
        if id_cible:
            bilan = obtenir_bilan_financier(id_cible, type_cible)
            
            st.divider()
            
            col1, col2, col3 =st.columns(3)
            col1.metric("💰 Total Facturé", f"{bilan['total_facture']:,.2f} MAD")
            col2.metric("💸 Total Encaissé", f"{bilan['total_paye']:,} MAD")
            
            #Coloration rouge si le reste est important
            reste = bilan['reste']
            col3.metric("🚨 Reste à Percevoir", f"{reste:,.2f} MAD", delta=-reste, delta_color="inverse")

        # 3 : BARRE DE PROGRESSION (VISUELLE) ---
        if bilan['total_facture'] > 0:
            taux = min(bilan['total_paye'] / bilan['total_facture'], 1.0)
            st.write(f"**Taux de recouvrement : {taux*100:.1f}%**")
            st.progress(taux)
        else:
            st.info("Aucune facture émise pour cette sélection.")

        # 4 : JOURNAL DES PAIEMENTS (DÉTAIL) ---
        st.subheader("📝 Journal des Règlements")
        
        # On récupère les paiements réels depuis la base
        query_pay = ""
        params = (id_cible,)
        
        if type_cible == "projet":
            query_pay = "SELECT date_paiement, montant_mad, mode_paiement, reference FROM payments WHERE id_project = ? ORDER BY date_paiement DESC"
        else:
            query_pay = """
                SELECT py.date_paiement, py.montant_mad, py.mode_paiement, py.reference 
                FROM payments py
                JOIN projects p ON py.id_project = p.id_project
                WHERE p.id_client = ?
                ORDER BY py.date_paiement DESC
            """
        
        try:
            conn = sqlite3.connect(DB_PATH)
            df_payments = pd.read_sql_query(query_pay, conn, params=params)
            conn.close()

            if not df_payments.empty:
                # Formatage propre des colonnes pour ton père
                df_payments.columns = ["Date", "Montant (MAD)", "Mode", "Référence"]
                st.dataframe(df_payments, use_container_width=True)
            else:
                st.write("Aucun paiement enregistré pour le moment.")
        except Exception as e:
            st.error(f"Erreur lors de la lecture des paiements : {e}")
        
        # 5 : CLÔTURE DU PROJET ---
        st.divider()
        if type_cible == "projet":
            # On vérifie si le projet n'est pas déjà clôturé
            # (Supposons que ta fonction obtenir_liste_projets_complet renvoie le statut en p[3])
            # Ici on simplifie en proposant l'action :
            
            if reste <= 0.01: # On laisse une marge pour les arrondis
                st.success("✅ Ce projet est totalement payé.")
                if st.button("📁 Clôturer et Archiver le Projet"):
                    success, msg = changer_statut_projet(id_cible, "Terminé", st.session_state['user_id'])
                    if success:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
            else:
                st.warning(f"⚠️ Il reste {reste:,.2f} MAD à percevoir avant de pouvoir clôturer ce dossier.")
                if st.checkbox("Forcer la clôture (Cas exceptionnel)"):
                    if st.button("📁 Archiver malgré l'impayé"):
                        changer_statut_projet(id_cible, "Clôturé avec impayé", st.session_state['user_id'])
                        st.rerun()

    elif choice == "Paramètres":
        if st.session_state['role'] != 'ADMIN':
            st.error("Accès interdit")
            st.stop()
            
        tab_lang, tab_user, tab_client, tab_logs = st.tabs([
        "🌐 Langue & Apparence", 
        "👥 Gestion Utilisateurs", 
        "🏢 Gestion Clients",
        "📜 Historique Global des Actions (Logs)"
        ])
        
        # --- SOUS-ONGLET 1 : LANGUE & APPARENCE ---
        with tab_lang:
            st.subheader("Préférences d'affichage")
            col1, col2 = st.columns(2)
            with col1:
                langue = st.radio("Sélectionner la langue :", ["Français", "العربية"], horizontal=True)
            with col2:
                theme = st.radio("Mode d'affichage :", ["Clair", "Sombre"], horizontal=True)
        
            if st.button("Enregistrer les préférences"):
                st.success(f"Paramètres mis à jour : {langue} / Mode {theme}")

        # --- SOUS-ONGLET 2 : GESTION UTILISATEURS ---
        with tab_user:
            # On déplace ici ton code existant pour créer/supprimer des utilisateurs
            st.subheader("👥 Contrôle des accès")
            # (Insère ici ton bloc actuel : add_user form et la liste avec supprimer_utilisateur)
            with st.expander("➕ Ajouter utilisateur"):
                with st.form("add_user"):
                    nom = st.text_input("Nom")
                    mail = st.text_input("Email")
                    mdp = st.text_input("Mot de passe", type="password")
                    rol = st.selectbox("Rôle", ["EMPLOYE", "ADMIN"])
    
                    if st.form_submit_button("Créer"):
                        if not mail or not mdp:
                            st.error("Champs obligatoires")
                        else:
                            creer_utilisateur(mail, mdp, rol, nom)
                            st.success("Ajouté")
                            st.rerun()

            st.subheader("Liste") 

            try:
                conn = sqlite3.connect(DB_PATH)
                df_u = pd.read_sql_query("SELECT nom_utilisateur, email, role FROM users", conn)
                conn.close()
            except Exception as e:
                st.error(f"Erreur DB : {e}")
                return

            for _, row in df_u.iterrows():  
                col1, col2 = st.columns([4,1])
                col1.write(f"{row['nom_utilisateur']} | {row['email']} ({row['role']})")

                if col2.button("Supprimer", key=row['email']):
                    success, msg = supprimer_utilisateur(row['email'])
                    if success:
                        st.success(msg)
                        st.rerun()
                        
        # --- SOUS-ONGLET 3 : GESTION CLIENTS ---
        with tab_client :
            st.subheader("Base de données de Clients")
            
            #Formulaire d'ajout de client
            with st.expander("➕ Ajouter un nouveau client"):
                with st.form("form_nouveau_client"):
                    n_client = st.text_input("Nom du client/entreprise") 
                    ice_client = st.text_input("ICE (Optionnel)")
                    num_tel = st.text_input("Numéro de téléphone ")
                    if st.form_submit_button("Ajouter le client"):
                       if n_client:
                        # Appel d'une fonction à ajouter dans db_manager
                        res, msg = ajouter_nouveau_client(n_client, ice_client, num_tel)
                        if res:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Le nom est obligatoire.")
                        
                
                st.divider()
                clients_db = obtenir_liste_clients()
                if clients_db:
                    for c in clients_db:
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"🏢 **{c['nom_client']}** | ICE: {c['ice_client']}")
                        if c2.button("Supprimer", key=f"del_c_{c['id_client']}"):
                        # Fonction à ajouter pour la suppression sécurisée
                            res, msg = supprimer_client_db(c['id_client'])
                            if res:
                                st.success(msg)
                                st.rerun()
    
        with tab_logs:
            df_logs = obtenir_historique_logs()
        
            if not df_logs.empty:
                # Renommer les colonnes pour que ce soit plus joli pour ton père
                df_logs.columns = ["Date & Heure", "Utilisateur", "Action", "Table", "Détails"]
            
                # Ajout d'un filtre de recherche rapide (par action ou utilisateur)
                recherche = st.text_input("🔍 Rechercher dans les logs (ex: 'UPDATE', 'Facture'...)")
                if recherche:
                    df_logs = df_logs[df_logs.apply(lambda row: recherche.lower() in row.astype(str).str.lower().values, axis=1)]

                # Affichage du tableau
                st.dataframe(
                    df_logs, 
                    use_container_width=True, 
                    hide_index=True
                )
            
                # Option pour vider les logs (uniquement pour l'Admin)
                if st.session_state.get('user_role') == 'ADMIN':
                    if st.button("🗑️ Purger l'historique (Action irréversible)"):
                        # Créer une fonction de suppression dans db_manager si nécessaire
                        st.warning("Fonctionnalité de purge en attente de confirmation.")
            else:
                st.info("Aucune action n'a encore été enregistrée dans le journal.")
                
# Lancement
if not st.session_state['auth_status']:
    login_page()
else :
    main_app()