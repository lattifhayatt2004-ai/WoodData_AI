# WoodData AI — Système Intelligent de Gestion de Menuiserie

**WoodData AI** est une solution métier "End-to-End" conçue pour **une entreprise de bois** afin de digitaliser et d'automatiser le cycle de vie complet des projets de menuiserie.

---

## 🗺️ Cartographie du Système (Project Architecture)

L'application est structurée autour de quatre piliers technologiques et fonctionnels :

### 1. Ingestion Intelligente (IA & NLP)
* **Technologie** : Gemini 1.5 Flash (Multimodal).
* **Fonction** : Extraction automatisée de données structurées (JSON) à partir de notes de chantiers, messages ou PDF.
* **Données extraites** : Désignation des articles, quantités, métrages linéaires (ML) et prix unitaires HT.

### 2. Moteur Financier (Business Logic)
* **Technologie** : Python (Decimal library).
* **Rigueur** : Gestion absolue des arrondis au centime près (règle $\ge 5$).
* **Calculs** : Automatisation des formules HT, TVA (20%) et TTC.
* **Contrôle de Cohérence** : Algorithme de gestion des reliquats empêchant de facturer au-delà du devis initial ($\sum \text{Factures} \le \text{Montant Devis}$).

### 3. Persistance & Modélisation (Data Layer)
* **Technologie** : SQLite.
* **Schéma Relationnel** : Architecture $1 \text{ Client} \rightarrow N \text{ Devis} \rightarrow N \text{ Factures/Paiements}$.
* **Traçabilité** : Chaque flux financier est imputé à un projet spécifique pour un audit en temps réel.

### 4. Interface & Reporting (User Experience)
* **Interface** : Dashboard Streamlit pour le suivi de la trésorerie et de l'avancement.
* **Reporting** : Moteur FPDF2 pour la génération de devis, factures de situation et états d'avancement conformes.
* **Légalité** : Intégration automatique des mentions de l'entreprise (ICE, RC, IF, Patente) et conversion des montants en toutes lettres.

---

## 🛠️ Stack Technique
| Composant | Technologie |
| :--- | :--- |
| **Backend** | Python 3.10+ |
| **Database** | SQLite |
| **LLM** | Gemini 1.5 Flash (API Google AI) |
| **Frontend** | Streamlit |
| **PDF** | FPDF2 |

---

## 🚀 État d'avancement (Project Roadmap)
* **Phase 1 : Fondations & Data** (Terminé) : Modélisation SQL et Moteur de calcul financier.
* **Phase 2 : Intelligence & Ingestion** (En cours) : Pipeline d'extraction multimodal et connecteur IA-DB.
* **Phase 3 : Interface & Visualisation** (Prévu) : Dashboard et Moteur de reporting PDF.
* **Phase 4 : Tests & Déploiement** (Prévu) : Validation finale sur données réelles.

---

## ⚖️ Mentions Légales Intégrées
Le système génère automatiquement les documents avec les identifiants fiscaux de l'entreprise :
* **ICE / RC / IF / Patente** 
* **Numérotation séquentielle des factures**
* **Montants TTC en toutes lettres**