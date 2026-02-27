from src.utils.finance import calculer_bilan_financier, verifier_reliquat, montant_en_lettres, arrondir
from decimal import Decimal

def test_system_financier():
    print("--- DEBUT DES TEST DE COHERENCE (JOUR2) ---")
    
    # tEST 1 : L'arrondi mathématique 
    # 10.005 doit arrondir à 10.01 et pas 10.00
    valeur_test = 10.005
    valeur_arrondie = arrondir(valeur_test)
    assert valeur_arrondie == Decimal("10.01"), f"Erreur d'arrondi : {valeur_arrondie} au lieu de 10.01"
    print("✅ Test 1 : Arrondi mathématique validé (10.005 -> 10.01).")
    
    # TEST 2 : Calcul du bilan financier
    # Montant total du devis : 750 000.00 MAD
    montant_devis_projet = 750000.00
    deja_facture = 500000.00
    nouvelle_facture = 250000.01
    
    autorise, message = verifier_reliquat(montant_devis_projet, deja_facture, nouvelle_facture)
    assert autorise is False, "Erreur : le système a laissé passer un dépassement !"
    
    print(f"✅ Test 2 : Blocage du dépassement validé. Message : {message}")
    
    # TEST 3 : Conversion en lettres
    montant_test = 123456.78
    montant_lettres = montant_en_lettres(montant_test)
    # On vérifie la présence des mots clés au lieu d'une phrase exacte
    assert "cent vingt-trois mille" in montant_lettres.lower()
    assert "dirhams" in montant_lettres.lower()
    assert "soixante-dix-huit" in montant_lettres.lower()
    
    print(f"✅ Test 3 : Conversion en lettres validée. Résultat : {montant_lettres}")
    
    print("\n--- TOUS LES TESTS SONT RÉUSSIS ! ---")
    
if __name__ == "__main__":
    test_system_financier()