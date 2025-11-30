from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class FactureOCRData(BaseModel):
    """Données extraites par OCR depuis la facture"""
    numero_facture: Optional[str] = None
    date_facture: Optional[str] = None
    fournisseur_nom: Optional[str] = None
    fournisseur_matricule: Optional[str] = None
    numero_po: Optional[str] = None
    montant_ht: Optional[float] = None
    montant_tva: Optional[float] = None
    montant_ttc: Optional[float] = None
    devise: str = "TND"
    type_achat: Optional[str] = None
    quantite: Optional[int] = None
    unite: Optional[str] = None
    specifications_techniques: Optional[str] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None


class ValidationResult(BaseModel):
    """Résultat de la validation facture vs PO"""
    is_valid: bool
    confidence_score: float = 0.0
    matched_fields: List[str] = []
    mismatches: List[Dict] = []
    warnings: List[str] = []
    errors: List[str] = []


class Facture(BaseModel):
    """Modèle complet de facture"""
    facture_id: str
    linked_po_id: str
    numero_facture: Optional[str] = None
    date_facture: Optional[str] = None
    date_reception: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Fournisseur
    fournisseur_nom: Optional[str] = None
    fournisseur_matricule: Optional[str] = None
    
    # Montants
    montant_ht: Optional[float] = None
    montant_tva: Optional[float] = None
    montant_ttc: Optional[float] = None
    devise: str = "TND"
    
    # Champs obligatoires pour comparaison avec PO
    type_achat: Optional[str] = None
    quantite: Optional[int] = None
    unite: Optional[str] = None
    centre_cout: Optional[str] = None
    priorite: Optional[str] = None
    delai_souhaite: Optional[str] = None
    date_livraison_souhaite: Optional[str] = None
    specifications_techniques: Optional[str] = None
    
    # Statut
    status: str = "En analyse"  # En analyse, Validée, Rejetée, Approuvée, Payée
    
    # OCR & Validation
    ocr_data: Optional[FactureOCRData] = None
    validation_result: Optional[ValidationResult] = None
    
    # Historique
    history: List[Dict] = []


class FactureCreate(BaseModel):
    linked_po_id: str
    image_url: str
    user_email: str