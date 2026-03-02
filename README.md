# 🪵 WoodData AI — Système Intelligent de Gestion de Menuiserie

**WoodData AI** est une solution métier "End-to-End" conçue pour digitaliser et automatiser le cycle de vie complet des projets de menuiserie pour l'entreprise **RM LUXE BOIS**.

---

## 🗺️ Cartographie du Système (Architecture)

L'application repose sur un pipeline robuste intégrant l'IA générative au cœur des processus financiers :

### 1. Ingestion Intelligente (IA & NLP)
* **Moteur** : Gemini 2.5 Flash / 1.5 Flash (via SDK `google-genai` 2026).
* **Fonction** : Extraction de données structurées (JSON) avec formatage sémantique (ex: **NOM** en gras).
* **Entités** : Désignation technique, Quantité, ML, PU HT.

### 2. Moteur Financier (Business Logic)
* **Technologie** : Python (Library `decimal`).
* **Précision** : Gestion stricte des arrondis au centime et conformité fiscale (TVA 20%).
* **Contrôle** : Algorithme anti-dépassement ($\sum \text{Factures} \le \text{Devis}$).

### 3. Persistance (Data Layer)
* **Database** : SQLite (`wooddata.db`).
* **Audit** : Système de `audit_logs` intégré pour tracer chaque mouvement financier.

---

## 🛠️ Stack Technique & Installation

| Composant | Technologie |
| :--- | :--- |
| **Langage** | Python 3.10+ |
| **IA SDK** | `google-genai` (v2026) |
| **Frontend** | Streamlit |
| **Database** | SQLite3 |

### Installation Rapide
1. Cloner le repository.
2. Installer les dépendances : `pip install -r requirements.txt`.
3. Configurer le secret : Créer `.streamlit/secrets.toml` et y ajouter votre `GEMINI_API_KEY`.

---

## 🚀 État d'avancement (Roadmap)

### ✅ Phase 1 : Fondations & Sécurité (TERMINÉ)
* Modélisation SQL (Tables Clients, Projets, Finance, Audit).
* Moteur de calcul financier (Logique Decimal).
* Système d'authentification et logs de sécurité.

### 🔄 Phase 2 : Ingestion & Intelligence (EN COURS)
* **Statut Jour 3** : Pipeline d'extraction fonctionnel (Test de cohérence validé).
* **Prochaine étape (Jour 4)** : Validation des schémas de données et mise en cache des requêtes IA.

### 📅 Phase 3 & 4 : Reporting & Déploiement (À VENIR)
* Moteur PDF (FPDF2) pour Devis/Factures.
* Dashboard de pilotage de trésorerie.

---

## ⚖️ Conformité & Gouvernance
Le système assure la génération de documents légaux incluant les mentions obligatoires de l'entreprise (ICE, RC, IF, Patente) et la conversion automatique des montants en toutes lettres.