"""
Routes API pour la gestion des départements - MongoDB
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from backend.models import (
    DepartmentCreate, DepartmentResponse, DepartmentUpdate, 
    DepartmentStatus, StandardResponse, convert_objectid_to_str
)
from config.database import get_database

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(dept: DepartmentCreate):
    """Créer un nouveau département"""
    db = get_database()
    
    # Vérifier que le code n'existe pas
    existing = await db.departments.find_one({"code": dept.code})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le code '{dept.code}' existe déjà"
        )
    
    dept_id = f"DEPT-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    dept_doc = {
        "id": dept_id,
        "name": dept.name,
        "code": dept.code,
        "manager": dept.manager,
        "email": dept.email,
        "description": dept.description,
        "status": DepartmentStatus.ACTIVE.value,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.departments.insert_one(dept_doc)
    
    created_dept = await db.departments.find_one({"id": dept_id})
    return convert_objectid_to_str(created_dept)

@router.get("/", response_model=List[DepartmentResponse])
async def list_departments():
    """Lister tous les départements actifs"""
    db = get_database()
    
    cursor = db.departments.find({"status": DepartmentStatus.ACTIVE.value})
    departments = await cursor.to_list(length=None)
    
    return [convert_objectid_to_str(d) for d in departments]

@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(dept_id: str):
    """Récupérer un département par ID"""
    db = get_database()
    
    dept = await db.departments.find_one({"id": dept_id})
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département '{dept_id}' non trouvé"
        )
    
    return convert_objectid_to_str(dept)

@router.get("/code/{code}", response_model=DepartmentResponse)
async def get_department_by_code(code: str):
    """Récupérer un département par code"""
    db = get_database()
    
    dept = await db.departments.find_one({"code": code.upper()})
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département avec code '{code}' non trouvé"
        )
    
    return convert_objectid_to_str(dept)

@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(dept_id: str, dept_update: DepartmentUpdate):
    """Mettre à jour un département"""
    db = get_database()
    
    dept = await db.departments.find_one({"id": dept_id})
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département '{dept_id}' non trouvé"
        )
    
    update_data = {
        "updated_at": datetime.utcnow()
    }
    
    if dept_update.name:
        update_data["name"] = dept_update.name
    if dept_update.manager:
        update_data["manager"] = dept_update.manager
    if dept_update.email:
        update_data["email"] = dept_update.email
    if dept_update.description is not None:
        update_data["description"] = dept_update.description
    
    await db.departments.update_one(
        {"id": dept_id},
        {"$set": update_data}
    )
    
    updated_dept = await db.departments.find_one({"id": dept_id})
    return convert_objectid_to_str(updated_dept)

@router.delete("/{dept_id}", response_model=StandardResponse)
async def delete_department(dept_id: str):
    """Supprimer un département (soft delete)"""
    db = get_database()
    
    dept = await db.departments.find_one({"id": dept_id})
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département '{dept_id}' non trouvé"
        )
    
    # Vérifier s'il y a des budgets associés
    budget = await db.budgets.find_one({"department_id": dept_id})
    if budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un département avec un budget associé"
        )
    
    # Soft delete: changer le statut à INACTIVE
    await db.departments.update_one(
        {"id": dept_id},
        {"$set": {"status": DepartmentStatus.INACTIVE.value, "updated_at": datetime.utcnow()}}
    )
    
    return StandardResponse(
        success=True,
        message=f"Département '{dept['name']}' supprimé avec succès",
        data={"department_id": dept_id}
    )
