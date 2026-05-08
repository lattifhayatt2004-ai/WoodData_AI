from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP

class WoodDataItem(BaseModel):
    """shéma d'une ligne devis/facture RM LUXE BOIS"""
    designation: str = Field(..., description = "Nom en gras + descriptif")
    quantite: float = Field(default=1.0, ge=0)
    ml: Optional[float] = Field(default=None, ge=0)
    pu_ht : Decimal = Field(..., ge=0)
    
    @field_validator('pu_ht', mode='before')
    @classmethod
    def validate_price(cls, v) :
        #Sécurité : force le format Decimal pour la précision financière
        #on s'arrondit à 2 décimales selon la règle commerciale (ROUND_HALF_UP)
        return Decimal(str(v)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    
class WoodDataResponse(BaseModel) :
    """shéma global de la réponse IA"""
    client: str = Field(..., min_length=2)
    lignes: List[WoodDataItem]
    
class FactureVentilation(BaseModel):
    id_item: int = Field(..., description="L'ID unique de l'article provenant du contexte")
    designation: str = Field(..., description="Nom de l'article pour vérification visuelle")
    montant_pris: Decimal = Field(..., ge=0, description="Montant exact prélevé sur cet article")

    @field_validator('montant_pris')
    def force_decimal_precision(cls, v):
        return Decimal(str(v)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    
class WoodDataInvoiceResponse(BaseModel):
    num_facture_propose: str = Field(..., pattern=r"^Facture-Client-\d{3}$")
    id_project: int
    montant_total_facture: Decimal
    ventilation: List[FactureVentilation]
    statut_comptable: str = Field("CONFORME", pattern="^(CONFORME|OVERFLOW_ERROR)$")