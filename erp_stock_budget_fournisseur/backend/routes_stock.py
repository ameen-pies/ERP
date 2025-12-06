"""
Routes API pour la gestion Stock & Comptabilité (BPMN Process 3) - MongoDB
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from backend.models import (
    StockItemCreate, StockItemResponse, StockMovementCreate, StockMovementResponse,
    MovementType, StandardResponse, convert_objectid_to_str
)
from config.database import get_database

router = APIRouter(prefix="/stock", tags=["Stock & Comptabilité"])

@router.post("/items", response_model=StockItemResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_item(item: StockItemCreate):
    """Création d'un nouvel article en stock"""
    db = get_database()
    
    # Vérifier si l'article existe
    existing = await db.stock.find_one({"item_id": item.item_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article {item.item_id} existe déjà"
        )
    
    stock_id = f"STK-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    item_doc = {
        "id": stock_id,
        "item_id": item.item_id,
        "item_name": item.item_name,
        "quantity": item.quantity,
        "unit": item.unit,
        "min_threshold": item.min_threshold,
        "unit_price": item.unit_price,
        "created_at": now,
        "last_updated": now
    }
    
    result = await db.stock.insert_one(item_doc)
    item_doc["_id"] = result.inserted_id
    
    return convert_objectid_to_str(item_doc)

@router.get("/items", response_model=List[StockItemResponse])
async def get_all_stock_items(low_stock_only: bool = False):
    """Récupération de tous les articles en stock"""
    db = get_database()
    
    query = {}
    if low_stock_only:
        # MongoDB aggregation to compare quantity with min_threshold
        cursor = db.stock.find({})
        items = await cursor.to_list(length=None)
        items = [item for item in items if item["quantity"] < item["min_threshold"]]
    else:
        cursor = db.stock.find({})
        items = await cursor.to_list(length=None)
    
    return [convert_objectid_to_str(item) for item in items]

@router.get("/items/{item_id}", response_model=StockItemResponse)
async def get_stock_item(item_id: str):
    """Récupération d'un article spécifique"""
    db = get_database()
    
    item = await db.stock.find_one({"item_id": item_id})
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {item_id} non trouvé"
        )
    
    return convert_objectid_to_str(item)

@router.post("/receive", response_model=StockMovementResponse)
async def receive_stock(movement: StockMovementCreate):
    """
    BPMN Process 3: Intégration Stock, Comptabilité & Projets
    """
    db = get_database()
    
    # Vérifier que l'article existe
    stock_item = await db.stock.find_one({"item_id": movement.item_id})
    
    if not stock_item:
        # Créer l'article automatiquement
        stock_id = f"STK-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        stock_item = {
            "id": stock_id,
            "item_id": movement.item_id,
            "item_name": f"Article {movement.item_id}",
            "quantity": 0.0,
            "unit": "pcs",
            "min_threshold": 10.0,
            "unit_price": movement.unit_price,
            "created_at": now,
            "last_updated": now
        }
        await db.stock.insert_one(stock_item)
    
    # Calculer le delta de quantité
    quantity_change = movement.quantity if movement.movement_type == MovementType.IN else -movement.quantity
    new_quantity = stock_item["quantity"] + quantity_change
    
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuffisant. Disponible: {stock_item['quantity']}, Demandé: {movement.quantity}"
        )
    
    # 1. MISE À JOUR STOCK
    await db.stock.update_one(
        {"item_id": movement.item_id},
        {
            "$set": {
                "quantity": new_quantity,
                "unit_price": movement.unit_price,
                "last_updated": datetime.utcnow()
            }
        }
    )
    
    total_value = movement.quantity * movement.unit_price
    
    # 2. GÉNÉRATION ÉCRITURE COMPTABLE
    entry_id = f"ACC-{uuid.uuid4().hex[:8].upper()}"
    
    if movement.movement_type == MovementType.IN:
        debit = f"Stock {movement.item_id}"
        credit = "Fournisseurs (Factures à recevoir)"
        entry_type = "RECEIPT"
    else:
        debit = "Coût des ventes"
        credit = f"Stock {movement.item_id}"
        entry_type = "DISPATCH"
    
    accounting_entry_doc = {
        "id": entry_id,
        "date": datetime.utcnow(),
        "entry_type": entry_type,
        "debit_account": debit,
        "credit_account": credit,
        "amount": total_value,
        "reference": movement.reference,
        "description": movement.description
    }
    await db.accounting_journal.insert_one(accounting_entry_doc)
    
    # 3. IMPUTATION COÛT PROJET
    project_msg = "Aucun projet lié"
    
    if movement.project_id:
        project = await db.projects.find_one({"project_id": movement.project_id})
        
        if not project:
            project_doc = {
                "project_id": movement.project_id,
                "total_cost": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.projects.insert_one(project_doc)
            project = project_doc
        
        new_total_cost = project["total_cost"] + total_value
        await db.projects.update_one(
            {"project_id": movement.project_id},
            {
                "$set": {
                    "total_cost": new_total_cost,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        project_msg = f"Coût imputé au projet {movement.project_id}: {total_value}€"
    
    # Enregistrer le mouvement
    movement_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    movement_doc = {
        "id": movement_id,
        "item_id": movement.item_id,
        "quantity": movement.quantity,
        "unit_price": movement.unit_price,
        "movement_type": movement.movement_type.value,
        "project_id": movement.project_id,
        "reference": movement.reference,
        "description": movement.description,
        "total_value": total_value,
        "created_at": now,
        "created_by": None
    }
    await db.stock_movements.insert_one(movement_doc)
    
    return StockMovementResponse(
        message="Transaction intégrée avec succès",
        stock_level=new_quantity,
        accounting_entry={
            "id": accounting_entry_doc["id"],
            "date": accounting_entry_doc["date"].isoformat() if isinstance(accounting_entry_doc["date"], datetime) else accounting_entry_doc["date"],
            "entry_type": accounting_entry_doc["entry_type"],
            "debit_account": accounting_entry_doc["debit_account"],
            "credit_account": accounting_entry_doc["credit_account"],
            "amount": accounting_entry_doc["amount"]
        },
        project_status=project_msg,
        movement={
            "id": movement_doc["id"],
            "item_id": movement_doc["item_id"],
            "quantity": movement_doc["quantity"],
            "unit_price": movement_doc["unit_price"],
            "movement_type": movement_doc["movement_type"],
            "total_value": movement_doc["total_value"],
            "created_at": movement_doc["created_at"].isoformat() if isinstance(movement_doc["created_at"], datetime) else movement_doc["created_at"]
        }
    )

@router.get("/movements")
async def get_stock_movements(
    item_id: str = None,
    movement_type: str = None,
    limit: int = 100
):
    """Récupération de l'historique des mouvements de stock"""
    db = get_database()
    
    query = {}
    if item_id:
        query["item_id"] = item_id
    if movement_type:
        query["movement_type"] = movement_type
    
    cursor = db.stock_movements.find(query).sort("created_at", -1).limit(limit)
    movements = await cursor.to_list(length=limit)
    
    return [
        {
            "id": m["id"],
            "item_id": m["item_id"],
            "quantity": m["quantity"],
            "unit_price": m["unit_price"],
            "movement_type": m["movement_type"],
            "project_id": m.get("project_id"),
            "total_value": m["total_value"],
            "created_at": m["created_at"].isoformat() if isinstance(m["created_at"], datetime) else m["created_at"]
        }
        for m in movements
    ]

@router.get("/accounting/journal")
async def get_accounting_journal(limit: int = 100):
    """Récupération du journal comptable"""
    db = get_database()
    
    cursor = db.accounting_journal.find({}).sort("date", -1).limit(limit)
    entries = await cursor.to_list(length=limit)
    
    return [
        {
            "id": e["id"],
            "date": e["date"].isoformat() if isinstance(e["date"], datetime) else e["date"],
            "entry_type": e["entry_type"],
            "debit_account": e["debit_account"],
            "credit_account": e["credit_account"],
            "amount": e["amount"],
            "reference": e.get("reference"),
            "description": e.get("description")
        }
        for e in entries
    ]

@router.get("/projects/{project_id}")
async def get_project_costs(project_id: str):
    """Récupération des coûts d'un projet"""
    db = get_database()
    
    project = await db.projects.find_one({"project_id": project_id})
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    
    cursor = db.stock_movements.find({"project_id": project_id})
    movements = await cursor.to_list(length=None)
    
    return {
        "project_id": project["project_id"],
        "total_cost": project["total_cost"],
        "movement_count": len(movements),
        "movements": [
            {
                "id": m["id"],
                "item_id": m["item_id"],
                "quantity": m["quantity"],
                "total_value": m["total_value"],
                "created_at": m["created_at"].isoformat() if isinstance(m["created_at"], datetime) else m["created_at"]
            }
            for m in movements
        ]
    }
