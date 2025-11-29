# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# ========== Shared small models ==========
class Demandeur(BaseModel):
    nom: str
    email: EmailStr

class Manager(BaseModel):
    nom: str
    email: EmailStr

class Fournisseur(BaseModel):
    nom: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None

class LigneBonCommande(BaseModel):
    numero_ligne: int
    description: str
    quantite: float
    unite: str
    prix_unitaire: float
    montant_ligne: float  # quantite * prix_unitaire
    reference_catalogue: Optional[str] = None
    specifications_techniques: Optional[str] = None

class HistoriqueAction(BaseModel):
    date: str = Field(default_factory=lambda: datetime.now().isoformat())
    action: str
    utilisateur: str
    details: Optional[str] = None

# ========== Bons de commande (BC) ==========
class LigneBonCommande(BaseModel):
    description: str
    quantite: float
    prix_unitaire: float
    montant_ligne: float
    unite: Optional[str] = "pcs"
    numero_ligne: Optional[int] = 1
    reference_catalogue: Optional[str] = None
    specifications_techniques: Optional[str] = None

class BonCommandeCreate(BaseModel):
    linked_pr_id: str
    details_demande: str
    justification: Optional[str] = ""
    type_achat: Optional[str] = "Produit"
    lignes: List[LigneBonCommande]

    # Make optional (frontend does NOT send them)
    devise: Optional[str] = "TND"
    demandeur: Optional[dict] = None
    manager: Optional[dict] = None
    fournisseur: Optional[dict] = None

    centre_cout: Optional[str] = None
    priorite: Optional[str] = "Moyenne"
    delai_souhaite: Optional[str] = None
    date_livraison_souhaitee: Optional[str] = None
    description_service: Optional[str] = None
    duree_contrat: Optional[str] = None
    mode_paiement: Optional[str] = None
    conditions_livraison: Optional[str] = None
    remarques: Optional[str] = None


# ========== Demande d'achat (PR) ==========
class DemandeAchatBase(BaseModel):
    id: str
    demandeur: str
    email_demandeur: EmailStr
    manager_email: Optional[EmailStr] = None
    type_achat: str
    details: str
    quantite: float
    unite: str
    prix_estime: float
    devise: str = "TND"
    fournisseur_suggere: Optional[str] = None
    centre_cout: Optional[str] = None
    priorite: str = "Moyenne"
    delai_souhaite: Optional[str] = None
    date_livraison_souhaitee: Optional[str] = None
    justification: Optional[str] = None
    specifications_techniques: Optional[str] = None
    description_service: Optional[str] = None
    duree_contrat: Optional[str] = None
    reference_catalogue: Optional[str] = None
    statut: str
    date_creation: str
    history: List[Dict[str, Any]] = []
    documents: List[str] = []
    validation_token: Optional[str] = None

    class Config:
        extra = "allow"

class DemandeAchatInDB(DemandeAchatBase):
    _id: Optional[Any] = None

# ========== PR models for main.py compatibility ==========
class PRBase(BaseModel):
    id: str
    demandeur: str
    email_demandeur: str
    type_achat: str
    details: str
    quantite: float
    unite: str
    prix_estime: float
    statut: str
    date_creation: str

class PRInDB(PRBase):
    _id: Optional[Any] = None
    manager_email: Optional[str] = None
    finance_email: Optional[str] = None
    fournisseur_suggere: Optional[str] = None
    priorite: Optional[str] = "Moyenne"
    specifications_techniques: Optional[str] = None
    history: List[Dict] = []

# ========== PO models (canonical, match frontend payload) ==========
class POCreate(BaseModel):
    prId: str
    items: str
    quantity: float
    unitPrice: float
    tax: float = 19.0
    supplier: str
    delivery: str

class POBase(BaseModel):
    id: str
    prId: str
    items: str
    quantity: float
    unitPrice: float
    tax: float
    amount: float
    supplier: str
    delivery: str
    status: str
    date: str
    workflow_id: Optional[str] = None

class POInDB(POBase):
    statut_workflow: Optional[str] = None
    details_pr: Optional[Dict] = None

class BonCommandeInDB(BonCommandeCreate):
    id: str
    montant_total_ht: float
    montant_tva: float
    montant_total_ttc: float
    status: str = "Brouillon"
    date_creation: str = Field(default_factory=lambda: datetime.now().isoformat())
    history: List[HistoriqueAction] = []
    documents: List[str] = []
    validation_token: Optional[str] = None
    workflow_id: Optional[str] = None
class StatusUpdate(BaseModel):
    status: str
    commentaire: Optional[str] = None
