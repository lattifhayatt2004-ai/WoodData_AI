# WoodData AI — Système Intelligent de Gestion pour RM LUXE BOIS

**WoodData AI** est une solution métier "End-to-End" conçue pour digitaliser et automatiser le cycle de vie complet des projets de menuiserie. Ce système transforme des notes de chantier brutes en données structurées et assure un suivi financier rigoureux.

---

## 🏗️ Architecture Technique (Fiche Spécificative)

Le projet est structuré selon une architecture découplée pour garantir la fiabilité des calculs et la persistance des données.

* **Interface** : Streamlit (Dashboard réactif et gestion des flux).
* **Base de données** : SQLite3 (Stockage local robuste).
* **Moteur IA** : Gemini 1.5 Flash (Analyse de notes de chantier et ventilation de factures via Prompt Engineering).
* **Traitement de Données** : Pandas (Reporting) et Decimal (Calculs financiers).

---

### 1. Moteur Financier (`src/utils/finance.py`)
Le "cerveau" mathématique du système, garantissant une précision comptable absolue :
* **Précision Décimale** : Utilisation de la bibliothèque `decimal` pour éviter les erreurs de flottants binaires.
* **Règle d'Arrondi Standard** : Implémentation de `ROUND_HALF_UP` (arrondi au centime supérieur si le 3ème chiffre ≥ 5).
* **Formules Métier Supportées** :
    - **QxPU** : Quantité × Prix Unitaire.
    - **MLxPU** : Mètre Linéaire × Prix Unitaire.
    - **QMLxPU** : Quantité × Mètre Linéaire × Prix Unitaire.
* **Conversion Textuelle** : Module `num2words` intégré pour la transcription des montants en toutes lettres sur les documents légaux.
* **`calculer_bilan_devis(lignes_ht, taux_tva)`** : Agrégateur financier. Calcule le Total HT, la TVA (20%) et le Total TTC global.
* **`generer_plan_ventilation(montant, articles)`** : L'algorithme de "Cascade". Reçoit un montant de facture et répartit l'argent article par article jusqu'à épuisement, en respectant les priorités d'ID.
* **`montant_en_lettres(nombre)`** : Moteur de transcription pour la validité juridique des documents.

### 2. Gestionnaire de Données (`src/db_manager.py`)
Le "bibliothécaire" gérant les interactions avec la base SQLite :
* **Persistance** : CRUD complet pour les Clients, Projets, Devis et Factures.
* **Sécurité RBAC** : Gestion des rôles (ADMIN/EMPLOYE) avec hachage des mots de passe (`sha256`).
* **Logique de Projet** : Un projet est défini par la validation d'un devis spécifique parmi plusieurs versions possibles.

---

### 3. Logique de "Monnaie" & Facturation
* **Facturation Séquentielle** : Algorithme de "Cascade" (remplissage des seaux) : un article n'est facturé que si le précédent est totalement soldé.
* **Audit Trail (Traçabilité)** : Table `audit_logs` enregistrant chaque modification sensible (ex: changement de montant de facture avec historique Ancien vs Nouveau).
* **Reliquats** : Calcul dynamique du "Reste à Facturer" (Devis vs Facture) et du "Reste à Percevoir" (Facture vs Paiement).

---

## 4. Spécifications du Schéma de Données (`init_db.sql`)

La base de données est normalisée pour éviter la redondance et permettre un audit complet :
* **`users`** : Gestion des accès RBAC (Admin/Employé) avec mots de passe hachés.
* **`estimates`** : Permet le versioning (v1, v2) d'un même projet avant validation.
* **`project_items`** : Stocke le détail technique (dimensions, type de calcul, prix unitaire).
* **`audit_logs`** : Journalise chaque événement critique du système.

---

## 5. Pipeline d'Intelligence Artificielle (Workflow Gemini)

L'intégration de Gemini 1.5 Flash suit un protocole de validation strict :
1.  **Extraction** : L'IA analyse les notes brutes et identifie les articles et prix.
2.  **Validation** : Le système affiche un aperçu via `st.data_editor` pour correction manuelle avant insertion.
3.  **Structuration** : Transformation des données en objets Python `Article` et `Devis` via le module `finance.py` pour garantir la conformité des calculs avant la sauvegarde SQL.

## 🚀 Fonctionnalités Clés Implémentées

* **Dashboard Admin** : Vue globale sur le CA Total, l'Encaissé et la Dette Client.
* **Extraction IA** : Transformation de texte brut en lignes de devis structurées avec validation manuelle.
* **Intervention Rapide** : Création de projets manuels avec validation immédiate pour les travaux urgents.
* **Reporting Avancé** : Analyse du taux de recouvrement par projet ou par client.
* **Versioning** : Historique des modifications financières pour une transparence totale.

---

## 📂 Structure du Projet

```text
WOODDATA_AI/
├── src/
│   ├── ai_engine/    # Moteur d'intelligence artificielle
│   ├── utils/       # finance.py (Calculs et conversions)
│   └── db_manager.py # Logic de base de données
├── database/        # wooddata.db & init_db.sql
├── assets/          # Logo_RMLB.png & ressources visuelles
└── app.py           # Point d'entrée Streamlit