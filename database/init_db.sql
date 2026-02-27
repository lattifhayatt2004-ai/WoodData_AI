-- 1. Table des Clients
CREATE TABLE IF NOT EXISTS clients (
    id_client INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_client TEXT NOT NULL,
    ice_client TEXT, -- Identifiant Commun de l'Entreprise (ICE)
    telephone_client TEXT
);

-- 2. Table des Devis / Projets
CREATE TABLE IF NOT EXISTS projects (
    id_project INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client INTEGER NOT NULL,
    nom_project TEXT NOT NULL,
    date_creation DATE DEFAULT CURRENT_DATE,
    address_project TEXT,
    total_ht REAL DEFAULT 0.0, -- Total Hors Taxes
    total_ttc REAL DEFAULT 0.0, -- Total Toutes Taxes Comprises
    FOREIGN KEY (id_client) REFERENCES clients(id_client)
);

-- 3. Table des Articles (Détail des devis)
CREATE TABLE IF NOT EXISTS project_items (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_project INTEGER NOT NULL,
    piece TEXT DEFAULT 'Général',
    designation TEXT NOT NULL,
    
    -- Les trois composantes du calcul [cite: 73, 74, 75]
    quantite REAL DEFAULT 1,     -- (Q)
    metrage REAL DEFAULT 0,      -- (ML)
    pu_ht REAL NOT NULL,         -- (PU)
    
    -- Le sélecteur de formule 
    -- 'QxPU'  : Quantité * Prix Unitaire
    -- 'MLxPU' : Métrage * Prix Unitaire 
    -- 'QMLxPU': Quantité * Métrage * Prix Unitaire
    calcul_type TEXT CHECK(calcul_type IN ('QxPU', 'MLxPU', 'QMLxPU')) DEFAULT 'QxPU',
    
    FOREIGN KEY (id_project) REFERENCES projects(id_project)
);

-- 4. Table des Factures (Invoices) de Situation
CREATE TABLE IF NOT EXISTS invoices (
    id_invoice INTEGER PRIMARY KEY AUTOINCREMENT,
    id_project INTEGER NOT NULL,
    num_facture TEXT UNIQUE NOT NULL, -- Format: 003/2026 
    montant_ttc REAL NOT NULL,
    date_facture DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_project) REFERENCES projects(id_project)
);

-- 5. Table des Paiements (Trésorerie)
CREATE TABLE IF NOT EXISTS payments (
    id_payment INTEGER PRIMARY KEY AUTOINCREMENT,
    id_invoice INTEGER NOT NULL,
    montant_mad REAL NOT NULL,
    type_paiement TEXT CHECK(type_paiement IN ('CHQ', 'VRT')), -- Chèque ou Virement
    date_paiement DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_invoice) REFERENCES invoices(id_invoice)
);

-- 6. Insertion des données légales de l'entreprise (RM LUXE BOIS)
-- Ces informations seront utilisées par FPDF2 pour les rapports
CREATE TABLE IF NOT EXISTS company_info (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Une seule ligne possible
    nom TEXT DEFAULT '**',
    ice TEXT DEFAULT '**',
    rc TEXT DEFAULT '**',
    patente TEXT DEFAULT '**',
    if_fiscal TEXT DEFAULT '**'
);

INSERT OR IGNORE INTO company_info (id, nom) VALUES (1, 'RM LUXE BOIS');