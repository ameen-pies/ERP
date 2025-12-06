"""
Routes API pour la gestion des fournisseurs (BPMN Process 1) - MongoDB
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from backend.models import (
    SupplierCreate, SupplierResponse, SupplierStatus, StandardResponse,
    convert_objectid_to_str
)
from config.database import get_database

router = APIRouter(prefix="/suppliers", tags=["Fournisseurs"])

@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(supplier: SupplierCreate):
    """
    Étape 1 BPMN: Création demande fournisseur + Contrôle doublons
    """
    db = get_database()
    
    # Vérification doublon par tax_id
    existing = await db.suppliers.find_one({"tax_id": supplier.tax_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Doublon détecté: Le numéro fiscal {supplier.tax_id} existe déjà"
        )
    
    # Création du nouveau fournisseur
    supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    supplier_doc = {
        "id": supplier_id,
        "name": supplier.name,
        "tax_id": supplier.tax_id,
        "category": supplier.category,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
        "status": SupplierStatus.PENDING_APPROVAL.value,
        "compliance_checked": True,
        "rejection_reason": None,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.suppliers.insert_one(supplier_doc)
    supplier_doc["_id"] = result.inserted_id
    
    return convert_objectid_to_str(supplier_doc)

@router.get("/", response_model=List[SupplierResponse])
async def get_all_suppliers(
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Récupération de la liste des fournisseurs avec filtres"""
    db = get_database()
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    cursor = db.suppliers.find(query).skip(skip).limit(limit)
    suppliers = await cursor.to_list(length=limit)
    
    return [convert_objectid_to_str(s) for s in suppliers]

@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str):
    """Récupération d'un fournisseur par ID"""
    db = get_database()
    
    # Try to find by custom id first
    supplier = await db.suppliers.find_one({"id": supplier_id})
    
    # Fallback: if not found, try searching by _id (for backward compatibility)
    if not supplier:
        try:
            from bson import ObjectId
            supplier = await db.suppliers.find_one({"_id": ObjectId(supplier_id)})
        except:
            pass
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fournisseur {supplier_id} non trouvé"
        )
    
    return convert_objectid_to_str(supplier)

@router.put("/{supplier_id}/validate", response_model=StandardResponse)
async def validate_supplier(supplier_id: str):
    """
    Étape 4 BPMN: Validation et activation du fournisseur
    """
    db = get_database()
    
    # Try to find by custom id first
    supplier = await db.suppliers.find_one({"id": supplier_id})
    
    # Fallback: if not found, try searching by _id (for backward compatibility)
    if not supplier:
        try:
            from bson import ObjectId
            supplier = await db.suppliers.find_one({"_id": ObjectId(supplier_id)})
        except:
            pass
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fournisseur {supplier_id} non trouvé"
        )
    
    if supplier["status"] != SupplierStatus.PENDING_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le fournisseur n'est pas en attente d'approbation (statut: {supplier['status']})"
        )
    
    # Determine the correct identifier to use for update
    # Use custom id if it exists, otherwise use _id
    update_query = {}
    if "id" in supplier and supplier["id"]:
        update_query = {"id": supplier["id"]}
        actual_supplier_id = supplier["id"]
    else:
        from bson import ObjectId
        update_query = {"_id": supplier["_id"]}
        actual_supplier_id = str(supplier["_id"])
    
    # Mise à jour du statut
    await db.suppliers.update_one(
        update_query,
        {
            "$set": {
                "status": SupplierStatus.ACTIVE.value,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return StandardResponse(
        success=True,
        message=f"Fournisseur {supplier['name']} activé avec succès",
        data={"supplier_id": actual_supplier_id, "new_status": "ACTIVE"}
    )

@router.put("/{supplier_id}/reject", response_model=StandardResponse)
async def reject_supplier(supplier_id: str, reason: str = None):
    """Rejet d'une demande fournisseur"""
    db = get_database()
    
    # Try to find by custom id first
    supplier = await db.suppliers.find_one({"id": supplier_id})
    
    # Fallback: if not found, try searching by _id (for backward compatibility)
    if not supplier:
        try:
            from bson import ObjectId
            supplier = await db.suppliers.find_one({"_id": ObjectId(supplier_id)})
        except:
            pass
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fournisseur non trouvé"
        )
    
    # Determine the correct identifier to use for update
    # Use custom id if it exists, otherwise use _id
    update_query = {}
    if "id" in supplier and supplier["id"]:
        update_query = {"id": supplier["id"]}
        actual_supplier_id = supplier["id"]
    else:
        from bson import ObjectId
        update_query = {"_id": supplier["_id"]}
        actual_supplier_id = str(supplier["_id"])
    
    await db.suppliers.update_one(
        update_query,
        {
            "$set": {
                "status": SupplierStatus.REJECTED.value,
                "rejection_reason": reason,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return StandardResponse(
        success=True,
        message="Demande fournisseur rejetée",
        data={"supplier_id": actual_supplier_id, "reason": reason}
    )

@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: str):
    """Suppression d'un fournisseur"""
    db = get_database()
    
    result = await db.suppliers.delete_one({"id": supplier_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fournisseur non trouvé"
        )
