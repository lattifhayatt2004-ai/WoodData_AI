-- 1. Table des Utilisateurs (Gestion RBAC par Hayat LATIF) 
CREATE TABLE IF NOT EXISTS users (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- Stockage sécurisé des mots de passe
    role TEXT CHECK(role IN ('ADMIN', 'EMPLOYE')) DEFAULT 'EMPLOYE',
    nom_utilisateur TEXT
);

-- 2. Table des Clients
CREATE TABLE IF NOT EXISTS clients (
    id_client INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_client TEXT NOT NULL,
    ice_client TEXT, -- Identifiant Commun de l'Entreprise (ICE)
    telephone_client TEXT
);

-- 3. Le Projet (Le dossier unique)
CREATE TABLE IF NOT EXISTS projects (
    id_project INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client INTEGER NOT NULL,
    nom_project TEXT NOT NULL,
    date_creation DATE DEFAULT CURRENT_DATE,
    address_project TEXT,
    statut_projet TEXT DEFAULT 'En Étude', -- ex: En Étude, En Cours, Terminé
    FOREIGN KEY (id_client) REFERENCES clients(id_client)
);

-- 4. Les Devis (Les versions de prix)
CREATE TABLE IF NOT EXISTS estimates (
    id_estimate INTEGER PRIMARY KEY AUTOINCREMENT,
    id_project INTEGER NOT NULL,
    version_numero INTEGER DEFAULT 1,
    date_devis DATE DEFAULT CURRENT_DATE,
    total_ht REAL DEFAULT 0.0,
    total_ttc REAL DEFAULT 0.0,
    est_valide BOOLEAN DEFAULT 0, -- 1 si c'est le devis accepté par RM LUXE BOIS et le client
    FOREIGN KEY (id_project) REFERENCES projects(id_project)
);

-- 5. Table des Articles (Détail des devis)
CREATE TABLE IF NOT EXISTS project_items (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estimate INTEGER NOT NULL, -- Changement ici (au lieu de id_project)
    piece TEXT DEFAULT 'Général',
    designation TEXT NOT NULL,
    quantite REAL DEFAULT 1.0,
    ml REAL DEFAULT 0.0,
    pu_ht REAL NOT NULL,
    type_calcul TEXT CHECK(type_calcul IN ('QxPU', 'MLxPU', 'QMLxPU')) DEFAULT 'QxPU',
    FOREIGN KEY (id_estimate) REFERENCES estimates(id_estimate) ON DELETE CASCADE
);

-- 6. Table des Factures (Invoices) de Situation
CREATE TABLE IF NOT EXISTS invoices (
    id_invoice INTEGER PRIMARY KEY AUTOINCREMENT,
    id_project INTEGER NOT NULL,
    num_facture TEXT UNIQUE NOT NULL, -- Format: 003/2026 
    montant_ttc REAL NOT NULL,
    date_facture DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_project) REFERENCES projects(id_project)
);

-- 7. Table des Paiements (Trésorerie)
CREATE TABLE IF NOT EXISTS payments (
    id_payment INTEGER PRIMARY KEY AUTOINCREMENT,
    id_invoice INTEGER NOT NULL,
    montant_mad REAL NOT NULL,
    type_paiement TEXT CHECK(type_paiement IN ('CHQ', 'VRT')), -- Chèque ou Virement
    date_paiement DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_invoice) REFERENCES invoices(id_invoice)
);

-- 9. JOURNAL D'AUDIT (Traçabilité totale exigée au CDC) 
CREATE TABLE IF NOT EXISTS audit_logs (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER, -- Qui a fait l'action
    action TEXT NOT NULL, -- ex: 'CREATE_INVOICE', 'UPDATE_PROJECT'
    table_nom TEXT,
    id_enregistrement INTEGER,
    details TEXT, -- Détails des changements (ex: Ancien prix vs Nouveau)
    date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES users(id_user)
);

-- 10. Table pour le suivi de l'avancement précis par article
CREATE TABLE IF NOT EXISTS invoice_line_details (
    id_detail INTEGER PRIMARY KEY AUTOINCREMENT,
    id_invoice INTEGER,
    id_project_item INTEGER,
    montant_alloue REAL, -- La part du montant de la facture affectée à cet article
    FOREIGN KEY (id_invoice) REFERENCES invoices(id_invoice),
    FOREIGN KEY (id_project_item) REFERENCES project_items(id_item)
);

-- 11. Insertion des données légales de l'entreprise (RM LUXE BOIS)
-- Ces informations seront utilisées par FPDF2 pour les rapports
CREATE TABLE IF NOT EXISTS company_info (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Une seule ligne possible
    nom TEXT DEFAULT 'RM LUXE BOIS',
    ice TEXT DEFAULT '003436221000011',
    rc TEXT DEFAULT '34569',
    patente TEXT DEFAULT '39501774',
    if_fiscal TEXT DEFAULT '60218199'
);


INSERT OR IGNORE INTO company_info (id, nom) VALUES (1, 'RM LUXE BOIS');