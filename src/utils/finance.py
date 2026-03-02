from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words
from dataclasses import dataclass
from typing import List

# 1. Modèles de Données
@dataclass
class Article:
    descriptif: str
    quantite: int = 1
    ml: float = 0.0
    pu_ht: float = 0.0
    calcul_type: str = "QxPU"
    
    def obtenir_montant_ht(self):
        """Calcule automatiquement le montant de la ligne via le moteur de calcul."""
        return calculer_ligne_ht(self.quantite, self.ml, self.pu_ht, self.calcul_type)

@dataclass
class Devis:
    client_id: int
    nom_projet: str
    articles: List[Article]
    
    def calculer_totaux(self):
        """Génère le bilan financier complet du devis."""
        lignes_ht = [art.obtenir_montant_ht() for art in self.articles]
        return calculer_bilan_devis(lignes_ht)

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
        result = Decimal(str(quantite)) * Decimal(str(pu_ht))
    elif type_calcul == "MLxPU" :
        result = Decimal(str(ml)) * Decimal(str(pu_ht))
    elif type_calcul == "QMLxPU" :
        result = Decimal(str(quantite)) * Decimal(str(ml)) * Decimal(str(pu_ht))
    else :
        result = Decimal("0")
    return arrondir(result)  
    
def calculer_bilan_devis(lignes_ht, taux_tva=0.20):
    """
    Calcule le total global HT, TVA et TTC avec une rigueur absolue[cite: 48].
    """
    total_ht = sum(lignes_ht)
    total_tva = total_ht * Decimal(str(taux_tva))
    total_ttc = total_ht + total_tva
    
    return {
        "total_ht": arrondir(total_ht),
        "total_tva": arrondir(total_tva),
        "total_ttc": arrondir(total_ttc)
    }

# 3. Algorithme de gestion des relicats
def valider_facture_situation(total_devis, total_deja_facture, nouveau_montant):
    """
    Vérifie si la facture ne dépasse pas le reste à facturer du devis[cite: 9, 51].
    """
    reliquat = Decimal(str(total_devis)) - Decimal(str(total_deja_facture))
    nouveau_montant = Decimal(str(nouveau_montant))
    
    if nouveau_montant > reliquat:
        return False, f"Dépassement de reliquat ! Maximum autorisé : {reliquat} MAD"
    
    return True, reliquat - nouveau_montant

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