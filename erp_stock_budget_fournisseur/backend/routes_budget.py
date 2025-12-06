"""
Routes API pour le contrôle budgétaire (BPMN Process 2) - MongoDB
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from datetime import datetime
import uuid

from backend.models import (
    BudgetCreate, BudgetResponse, BudgetCheckRequest, BudgetCheckResponse,
    BudgetStatus, StandardResponse, convert_objectid_to_str
)
from config.database import get_database

router = APIRouter(prefix="/budget", tags=["Budget"])

@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(budget: BudgetCreate):
    """Création d'un nouveau budget départemental"""
    db = get_database()
    
    # Vérifier si le département existe déjà
    existing = await db.budgets.find_one({"department": budget.department})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget pour {budget.department} existe déjà"
        )
    
    budget_id = f"BDG-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    budget_doc = {
        "id": budget_id,
        "department": budget.department,
        "allocated": budget.allocated,
        "used": budget.used,
        "available": budget.allocated - budget.used,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.budgets.insert_one(budget_doc)
    budget_doc["_id"] = result.inserted_id
    
    return convert_objectid_to_str(budget_doc)

@router.get("/", response_model=List[BudgetResponse])
async def get_all_budgets():
    """Récupération de tous les budgets"""
    db = get_database()
    
    cursor = db.budgets.find({})
    budgets = await cursor.to_list(length=None)
    
    return [convert_objectid_to_str(b) for b in budgets]

@router.get("/status", response_model=Dict[str, dict])
async def get_budget_status():
    """Vue d'ensemble des budgets par département"""
    db = get_database()
    
    cursor = db.budgets.find({})
    budgets = await cursor.to_list(length=None)
    
    status_dict = {}
    for budget in budgets:
        status_dict[budget["department"]] = {
            "allocated": budget["allocated"],
            "used": budget["used"],
            "available": budget["allocated"] - budget["used"],
            "usage_percentage": round((budget["used"] / budget["allocated"]) * 100, 2) if budget["allocated"] > 0 else 0
        }
    
    return status_dict

@router.post("/check", response_model=BudgetCheckResponse)
async def check_budget_compliance(request: BudgetCheckRequest):
    """
    BPMN Process 2: Contrôle budgétaire automatisé
    """
    db = get_database()
    
    # Récupération du budget départemental
    budget = await db.budgets.find_one({"department": request.department})
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département {request.department} non trouvé"
        )
    
    available = budget["allocated"] - budget["used"]
    
    # Étape 2 BPMN: Vérification budget suffisant
    if request.amount > available:
        return BudgetCheckResponse(
            status=BudgetStatus.REJECTED,
            reason="Budget Insuffisant",
            details=f"Disponible: {available}€, Demandé: {request.amount}€"
        )
    
    # Étape 3 BPMN: Vérification règles métier
    THRESHOLD_APPROVAL = 10000.0
    
    if request.amount > THRESHOLD_APPROVAL:
        # Créer une demande en attente
        transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"
        pending_trx = {
            "id": transaction_id,
            "department": request.department,
            "amount": request.amount,
            "description": request.description,
            "reference": request.reference,
            "status": "PENDING_APPROVAL",
            "created_at": datetime.utcnow()
        }
        await db.pending_transactions.insert_one(pending_trx)
        
        return BudgetCheckResponse(
            status=BudgetStatus.BLOCKED,
            reason="Validation Hiérarchique Requise",
            details=f"Montant > {THRESHOLD_APPROVAL}€ nécessite validation DAF",
            transaction_id=transaction_id
        )
    
    # Étape 7 BPMN: Mise à jour du budget
    new_used = budget["used"] + request.amount
    new_available = budget["allocated"] - new_used
    
    await db.budgets.update_one(
        {"department": request.department},
        {
            "$set": {
                "used": new_used,
                "available": new_available,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Enregistrer la transaction
    transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"
    transaction = {
        "id": transaction_id,
        "department": request.department,
        "amount": request.amount,
        "description": request.description,
        "reference": request.reference,
        "status": "VALIDATED",
        "created_at": datetime.utcnow()
    }
    await db.budget_transactions.insert_one(transaction)
    
    return BudgetCheckResponse(
        status=BudgetStatus.VALIDATED,
        details="Transaction validée et budget mis à jour",
        new_available=new_available,
        transaction_id=transaction_id
    )

@router.get("/transactions")
async def get_budget_transactions(department: str = None, limit: int = 50):
    """Récupération de l'historique des transactions budgétaires"""
    db = get_database()
    
    query = {}
    if department:
        query["department"] = department
    
    cursor = db.budget_transactions.find(query).sort("created_at", -1).limit(limit)
    transactions = await cursor.to_list(length=limit)
    
    return [
        {
            "id": t["id"],
            "department": t["department"],
            "amount": t["amount"],
            "description": t["description"],
            "reference": t.get("reference"),
            "status": t["status"],
            "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"]
        }
        for t in transactions
    ]

@router.put("/{department}/reset", response_model=StandardResponse)
async def reset_budget(department: str):
    """Réinitialiser le budget utilisé d'un département"""
    db = get_database()
    
    budget = await db.budgets.find_one({"department": department})
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Département non trouvé"
        )
    
    await db.budgets.update_one(
        {"department": department},
        {
            "$set": {
                "used": 0.0,
                "available": budget["allocated"],
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return StandardResponse(
        success=True,
        message=f"Budget {department} réinitialisé",
        data={"department": department}
    )
