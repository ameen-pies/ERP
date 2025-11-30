from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class TypeAchat(str, Enum):
    ARTICLE = "Article"
    SERVICE = "Service"
    CAPEX = "CAPEX"
    CONTRAT = "Contrat"
    CATALOGUE = "Catalogue"

class StatutPR(str, Enum):
    BROUILLON = "Brouillon"
    EN_VALIDATION_HIERARCHIQUE = "En validation hiérarchique"
    VALIDEE = "Validée"
    ACTIVE = "Active"
    REJETEE = "Rejetée"
    ARCHIVEE = "Archivée"

class Document(BaseModel):
    filename: str
    content_type: str
    data: bytes

class PRBase(BaseModel):
    demandeur: str
    email_demandeur: str
    type_achat: TypeAchat
    details: str
    quantite: Optional[int] = None
    unite: Optional[str] = None
    prix_estime: Optional[float] = None
    fournisseur_suggere: Optional[str] = None
    centre_cout: Optional[str] = None
    priorite: str = "Moyenne"
    delai_souhaite: Optional[str] = None
    justification: Optional[str] = None
    # Dynamic fields based on type
    specifications_techniques: Optional[str] = None  # For Article/CAPEX
    description_service: Optional[str] = None  # For Service
    duree_contrat: Optional[str] = None  # For Contrat
    reference_catalogue: Optional[str] = None  # For Catalogue

class PR(PRBase):
    id: str
    statut: StatutPR = StatutPR.BROUILLON
    date_creation: datetime = Field(default_factory=datetime.now)
    history: List[dict] = []
    documents: List[Document] = []
    manager_email: Optional[str] = None
    finance_email: Optional[str] = None
    validation_token: Optional[str] = None

class PRCreate(PRBase):
    manager_email: str
    finance_email: str

class PRResponse(BaseModel):
    id: str
    demandeur: str
    type_achat: str
    details: str
    statut: str
    date_creation: str
    centre_cout: Optional[str]
    priorite: str
    prix_estime: Optional[float]