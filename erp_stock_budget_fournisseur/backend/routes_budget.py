"""
Routes API pour le contrôle budgétaire (BPMN Process 2) - MongoDB
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from datetime import datetime
import uuid

from backend.models import (
    BudgetCreate, BudgetResponse, BudgetUpdate, BudgetCheckRequest, BudgetCheckResponse,
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
    
    # Créer la réponse correcte avec dates en ISO format
    response = {
        "id": budget_doc["id"],
        "department": budget_doc["department"],
        "allocated": budget_doc["allocated"],
        "used": budget_doc["used"],
        "available": budget_doc["available"],
        "created_at": budget_doc["created_at"].isoformat() if isinstance(budget_doc["created_at"], datetime) else str(budget_doc["created_at"]),
        "updated_at": budget_doc["updated_at"].isoformat() if isinstance(budget_doc["updated_at"], datetime) else str(budget_doc["updated_at"])
    }
    
    return response

@router.get("/", response_model=List[BudgetResponse])
async def get_all_budgets():
    """Récupération de tous les budgets"""
    db = get_database()
    
    cursor = db.budgets.find({})
    budgets = await cursor.to_list(length=None)
    
    # Convertir les ObjectId en string et formater la réponse
    result = []
    for b in budgets:
        created_at = b.get("created_at")
        updated_at = b.get("updated_at")
        result.append({
            "id": b.get("id") or str(b.get("_id")),
            "department": b.get("department"),
            "allocated": b.get("allocated"),
            "used": b.get("used"),
            "available": b.get("available"),
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
            "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at)
        })
    
    return result

@router.get("/status", response_model=Dict[str, dict])
async def get_budget_status():
    """Vue d'ensemble des budgets par département"""
    db = get_database()
    
    cursor = db.budgets.find({})
    budgets = await cursor.to_list(length=None)
    
    status_dict = {}
    for budget in budgets:
        # Vérifier que department existe
        if "department" not in budget:
            continue
        status_dict[budget["department"]] = {
            "allocated": budget.get("allocated", 0),
            "used": budget.get("used", 0),
            "available": budget.get("available", budget.get("allocated", 0) - budget.get("used", 0)),
            "usage_percentage": round((budget.get("used", 0) / budget.get("allocated", 1)) * 100, 2) if budget.get("allocated", 0) > 0 else 0
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

@router.put("/update/{budget_id}", response_model=BudgetResponse)
async def update_budget(budget_id: str, data: BudgetUpdate):
    """Mettre à jour un budget (allocated et/ou used)"""
    db = get_database()
    
    budget = await db.budgets.find_one({"id": budget_id})
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} non trouvé"
        )
    
    # Préparer les updates
    updates = {}
    if data.allocated is not None:
        updates["allocated"] = data.allocated
    if data.used is not None:
        updates["used"] = data.used
    
    # Calculer le montant disponible si nécessaire
    if updates:
        new_allocated = updates.get("allocated", budget.get("allocated", 0))
        new_used = updates.get("used", budget.get("used", 0))
        updates["available"] = new_allocated - new_used
        updates["updated_at"] = datetime.utcnow()
        
        await db.budgets.update_one(
            {"id": budget_id},
            {"$set": updates}
        )
    
    # Récupérer le budget mis à jour
    updated_budget = await db.budgets.find_one({"id": budget_id})
    
    # Formater la réponse
    return {
        "id": updated_budget["id"],
        "department": updated_budget["department"],
        "allocated": updated_budget["allocated"],
        "used": updated_budget["used"],
        "available": updated_budget["available"],
        "created_at": updated_budget["created_at"].isoformat() if isinstance(updated_budget["created_at"], datetime) else str(updated_budget["created_at"]),
        "updated_at": updated_budget["updated_at"].isoformat() if isinstance(updated_budget["updated_at"], datetime) else str(updated_budget["updated_at"])
    }

@router.put("/reset/{department}", response_model=StandardResponse)
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
