from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words
from dataclasses import dataclass
from typing import List

# 1. Modèles de Données
@dataclass
class Article:
    descriptif: str
    quantite: int
    ml: float
    pu_ht: float
    calcul_type: str

@dataclass
class Devis:
    client_id: int
    nom_projet: str
    articles: List[Article]

# 2. Implémentation du Moteur de Calcul (HT, TVA, TTC)
def arrondir(valeur) :
    """
    Applique l'arrondi mathématique standard : 
    si le 3ème chiffre >= 5, on arrondit au centime supérieur.
    """
    return Decimal(str(valeur)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

def calculer_ligne_ht(quantite, ml, pu_ht, type_calcul="QxPU") :
    """
    Calculer le montant HT d'une ligne (Article) selon la formule métier.
    Types : 
    - QxPU : Quantité x Prix Unitaire
    - MLxPU : Mètre Linéaire x Prix Unitaire
    - QMLxPU : Quantité x Mètre Linéaire x Prix Unitaire
    """
    if type_calcul == "QxPU" :
        result = quantite * pu_ht
    elif type_calcul == "MLxPU" :
        result = ml * pu_ht
    elif type_calcul == "QMLxPU" :
        result = quantite * ml * pu_ht
    else :
        result = 0
    return arrondir(result)  
    
def calculer_bilan_financier(lignes_ht, taux_tva=0.20) :
    """
    Calcule les totaux globales avec arrondi au centime près
    """
    total_ht = sum(lignes_ht)
    total_ht_arrondi = arrondir(total_ht)
    # Calcul du total TVA
    total_tva = total_ht_arrondi * Decimal(str(taux_tva))
    total_tva_arrondi = arrondir(total_tva)
    # Calcul du total TTC
    total_ttc = total_ht_arrondi + total_tva_arrondi
    return {
            "total_ht": float(total_ht_arrondi),
            "total_tva": float(total_tva_arrondi),
            "total_ttc": float(total_ttc)
    }

# 3. Algorithme de gestion des relicats
def verifier_reliquat(montant_article, total_deja_facture, nouveau_montant_facture):
    """
    Vérifie si la nouvelle facture ne dépasse pas le reliquat de l'article
    """
    reliquat = montant_article - total_deja_facture
    if nouveau_montant_facture > reliquat:
        return False, f"Dépassement de reliquaat ! Disponible : {reliquat} MAD "
    return True, reliquat-nouveau_montant_facture

# 4. Module de Conversion en Toutes Lettres
def montant_en_lettres(montant) :
    """
    Transforme un montant numérique en lettres
    """
    entier = int(montant)
    centimes = int(round((montant - entier) * 100))
    texte = num2words(entier, lang='fr') + " dirhams"
    if centimes > 0 :
        texte += " et " + num2words(centimes, lang='fr') + " centimes"
        
    return texte.capitalize()