from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
from workflow_models import *
import motor.motor_asyncio
import httpx
import os
from dotenv import load_dotenv
from pathlib import Path
import traceback
import json
from bson import ObjectId

load_dotenv()

app = FastAPI(title="Système de Workflow d'Approbation Collaboratif - Module 4")

def clean_mongo_doc(doc):
    """Remove MongoDB-specific fields and convert to JSON-serializable format"""
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [clean_mongo_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        doc.pop('_id', None)
        cleaned = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, (dict, list)):
                cleaned[key] = clean_mongo_doc(value)
            else:
                cleaned[key] = value
        return cleaned
    
    return doc

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "ERP")

if not MONGODB_URL:
    raise Exception("❌ MONGODB_URL not found in .env file")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

PO_SERVICE_URL = "http://localhost:8000"
BASE_DIR = Path(__file__).resolve().parent

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ WebSocket déconnecté. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        print(f"📢 Diffusion à {len(self.active_connections)} connexions: {message.get('type')}")
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Échec d'envoi à la connexion: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

MOCK_USERS = {
    "tech_lead_1": {"name": "Alice Tech", "email": "alice@company.com", "department": "IT", "roles": [ApprovalRole.TECHNICAL_REVIEWER]},
    "it_manager_1": {"name": "Bob IT Manager", "email": "bob@company.com", "department": "IT", "roles": [ApprovalRole.DEPARTMENT_MANAGER]},
    "finance_1": {"name": "Charlie Finance", "email": "charlie@company.com", "department": "Finance", "roles": [ApprovalRole.FINANCIAL_APPROVER]},
    "purchasing_1": {"name": "Diana Purchasing", "email": "diana@company.com", "department": "Achats", "roles": [ApprovalRole.PURCHASING_MANAGER]},
    "gm_1": {"name": "Eve General Manager", "email": "eve@company.com", "department": "Direction", "roles": [ApprovalRole.GENERAL_MANAGER]},
    "user_1": {"name": "Frank User", "email": "frank@company.com", "department": "IT", "roles": []},
    "John Doe": {"name": "John Doe", "email": "john@company.com", "department": "IT", "roles": []},
    "Jane Smith": {"name": "Jane Smith", "email": "jane@company.com", "department": "RH", "roles": []}
}

@app.on_event("startup")
async def startup_event():
    try:
        await client.admin.command('ping')
        print("✅ Module 4: Connecté à MongoDB Atlas")
        print(f"📊 Utilisation de la base de données: {DATABASE_NAME}")
        print(f"📁 Répertoire de base: {BASE_DIR}")
        
        ui_path = BASE_DIR / "ui.html"
        if ui_path.exists():
            print(f"✅ ui.html trouvé à: {ui_path}")
        else:
            print(f"❌ ui.html NON trouvé à: {ui_path}")
    except Exception as e:
        print(f"❌ Module 4: Échec de connexion à MongoDB: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    client.close()
    print("❌ Module 4: Connexion MongoDB fermée")

@app.get("/")
async def root():
    """Servir l'interface principale"""
    ui_path = BASE_DIR / "ui.html"
    if ui_path.exists():
        return FileResponse(ui_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Fichier UI introuvable")

@app.get("/ui.html")
async def serve_ui():
    """Servir le fichier HTML de l'interface"""
    ui_path = BASE_DIR / "ui.html"
    if ui_path.exists():
        return FileResponse(ui_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="ui.html introuvable")

@app.get("/health")
async def health_check():
    """Point de terminaison de vérification de santé"""
    ui_exists = (BASE_DIR / "ui.html").exists()
    return {
        "status": "sain",
        "module": "Module 4 - Workflow",
        "ui_html_exists": ui_exists,
        "base_dir": str(BASE_DIR),
        "database": DATABASE_NAME
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📨 Message WS reçu: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        manager.disconnect(websocket)

def get_required_approvers(department: str, amount: float = 0) -> List[ApprovalRole]:
    """Déterminer les approbateurs requis en fonction du département et du montant"""
    base_approvers = [ApprovalRole.DEPARTMENT_MANAGER]
    
    if amount > 1000:
        base_approvers.append(ApprovalRole.FINANCIAL_APPROVER)
    if amount > 5000:
        base_approvers.append(ApprovalRole.PURCHASING_MANAGER)
    if amount > 20000:
        base_approvers.append(ApprovalRole.GENERAL_MANAGER)
    
    if department == "IT" and amount > 500:
        base_approvers.insert(0, ApprovalRole.TECHNICAL_REVIEWER)
    
    return base_approvers

def find_approver_user(role: ApprovalRole, department: str) -> Optional[Dict[str, Any]]:
    """Trouver un utilisateur qui peut remplir le rôle d'approbation donné"""
    for user_id, user_data in MOCK_USERS.items():
        if role in user_data["roles"]:
            return {"user_id": user_id, **user_data}
    return None

@app.post("/workflows", response_model=ApprovalWorkflow)
async def create_workflow(workflow_data: WorkflowCreate, background_tasks: BackgroundTasks):
    """Créer un nouveau workflow d'approbation"""
    try:
        existing = await db.workflows.find_one({"document_id": workflow_data.document_id})
        if existing:
            raise HTTPException(status_code=400, detail="Un workflow existe déjà pour ce document")
        
        required_roles = get_required_approvers(
            workflow_data.department, 
            workflow_data.total_amount or 0
        )
        
        steps = []
        for i, role in enumerate(required_roles):
            approver = find_approver_user(role, workflow_data.department)
            if approver:
                step = ApprovalStep(
                    step_id=f"step_{i+1}",
                    role=role,
                    assigned_to=approver["user_id"],
                    assigned_name=approver["name"],
                    deadline=(datetime.now() + timedelta(days=3)).isoformat(),
                    order=i
                )
                steps.append(step.dict())
        
        workflow_id = f"WF-{uuid.uuid4().hex[:8].upper()}"
        workflow = ApprovalWorkflow(
            workflow_id=workflow_id,
            document_type=workflow_data.document_type,
            document_id=workflow_data.document_id,
            document_title=workflow_data.document_title,
            initiator=workflow_data.initiator,
            initiator_name=workflow_data.initiator_name,
            department=workflow_data.department,
            total_amount=workflow_data.total_amount,
            steps=steps
        )
        
        if steps:
            steps[0]["status"] = ApprovalStatus.IN_PROGRESS
            workflow.steps = steps
        
        workflow_dict = workflow.dict()
        await db.workflows.insert_one(workflow_dict)
        
        await manager.broadcast({
            "type": "workflow_created",
            "data": workflow_dict
        })
        
        print(f"✅ Workflow {workflow_id} créé pour {workflow_data.document_id}")
        
        return clean_mongo_doc(workflow_dict)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la création du workflow: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/{workflow_id}", response_model=ApprovalWorkflow)
async def get_workflow(workflow_id: str):
    """Obtenir les détails du workflow"""
    try:
        workflow = await db.workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable")
        return clean_mongo_doc(workflow)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention du workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/document/{document_id}")
async def get_workflow_by_document(document_id: str):
    """Obtenir le workflow par ID de document"""
    try:
        workflow = await db.workflows.find_one({"document_id": document_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable pour ce document")
        return clean_mongo_doc(workflow)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention du workflow par document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/user/{user_id}/pending")
async def get_pending_approvals(user_id: str):
    """Obtenir toutes les approbations en attente pour un utilisateur"""
    try:
        workflows = []
        async for workflow in db.workflows.find({
            "overall_status": {"$in": ["pending", "in_progress"]},
            "steps": {
                "$elemMatch": {
                    "assigned_to": user_id,
                    "status": {"$in": ["pending", "in_progress"]}
                }
            }
        }):
            workflows.append(clean_mongo_doc(workflow))
        
        print(f"📋 Trouvé {len(workflows)} workflows en attente pour l'utilisateur {user_id}")
        return workflows
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention des approbations en attente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CRITICAL FIXES FOR MODULE 4 (main.py)
# Replace the take_workflow_action endpoint with this corrected version:

@app.post("/workflows/{workflow_id}/action")
async def take_workflow_action(
    workflow_id: str, 
    action_request: ApprovalActionRequest,
    background_tasks: BackgroundTasks
):
    """
    Take action on a workflow step
    FIXED: Proper handling of REQUEST_CHANGES to freeze workflow
    """
    try:
        print(f"📄 Processing action for workflow {workflow_id}: {action_request.action}")
        
        workflow = await db.workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow non trouvé")
        
        # Find step
        step_index = -1
        for i, step in enumerate(workflow["steps"]):
            if step["step_id"] == action_request.step_id:
                step_index = i
                break
        
        if step_index == -1:
            raise HTTPException(status_code=404, detail="Étape non trouvée dans le workflow")
        
        # 1️⃣ Handle DELEGATION (must be first)
        if action_request.action == ApprovalAction.DELEGATE and action_request.delegate_to:
            delegate_user = MOCK_USERS.get(action_request.delegate_to)
            if not delegate_user:
                raise HTTPException(status_code=400, detail="Utilisateur de délégation invalide")
            
            workflow["steps"][step_index]["assigned_to"] = action_request.delegate_to
            workflow["steps"][step_index]["assigned_name"] = delegate_user["name"]
            workflow["steps"][step_index]["comments"] = f"Délégué à {delegate_user['name']}. {action_request.comments}"
            workflow["steps"][step_index]["action_date"] = datetime.now().isoformat()
            workflow["steps"][step_index]["status"] = ApprovalStatus.IN_PROGRESS
            print(f"🔄 Step {step_index + 1} delegated to {action_request.delegate_to}")
        
        # 2️⃣ Handle APPROVE
        elif action_request.action == ApprovalAction.APPROVE:
            workflow["steps"][step_index]["action"] = action_request.action
            workflow["steps"][step_index]["comments"] = action_request.comments
            workflow["steps"][step_index]["action_date"] = datetime.now().isoformat()
            workflow["steps"][step_index]["status"] = ApprovalStatus.APPROVED
            print(f"✅ Step {step_index + 1} approved")
            
            # Move to next step if approved
            if step_index < len(workflow["steps"]) - 1:
                workflow["current_step"] = step_index + 1
                workflow["steps"][step_index + 1]["status"] = ApprovalStatus.IN_PROGRESS
                print(f"➡️ Moving to step {step_index + 2}")
            else:
                # All steps approved - workflow completed
                workflow["overall_status"] = ApprovalStatus.COMPLETED
                print(f"🎉 Workflow {workflow_id} completed!")
                
                # Notify Module 3 that BC is APPROVED
                background_tasks.add_task(
                    notify_po_service_approved,
                    workflow["document_id"],
                    workflow["workflow_id"]
                )
        
        # 3️⃣ Handle REJECT
        elif action_request.action == ApprovalAction.REJECT:
            workflow["steps"][step_index]["action"] = action_request.action
            workflow["steps"][step_index]["comments"] = action_request.comments
            workflow["steps"][step_index]["action_date"] = datetime.now().isoformat()
            workflow["steps"][step_index]["status"] = ApprovalStatus.REJECTED
            workflow["overall_status"] = ApprovalStatus.REJECTED
            print(f"❌ Step {step_index + 1} rejected - workflow rejected")
            
            # Notify Module 3 that BC is REJECTED
            background_tasks.add_task(
                notify_po_service_rejected,
                workflow["document_id"],
                workflow["workflow_id"],
                action_request.comments
            )
        
        # 4️⃣ Handle REQUEST_CHANGES (CRITICAL FIX)
        elif action_request.action == ApprovalAction.REQUEST_CHANGES:
            workflow["steps"][step_index]["action"] = action_request.action
            workflow["steps"][step_index]["comments"] = action_request.comments
            workflow["steps"][step_index]["action_date"] = datetime.now().isoformat()
            workflow["steps"][step_index]["status"] = ApprovalStatus.CHANGES_REQUESTED
            workflow["overall_status"] = ApprovalStatus.CHANGES_REQUESTED
            
            # CRITICAL: Keep workflow frozen at current step
            # Do NOT reset steps here - that happens on restart
            workflow["current_step"] = step_index
            
            # Notify Module 3 to put BC back to DRAFT and PR back to Active
            background_tasks.add_task(
                notify_po_service_changes_requested,
                workflow["document_id"],
                workflow["workflow_id"],
                action_request.comments
            )
            print(f"✏️ Changes requested - BC set to draft, PR reactivated")
        
        # Update timestamp
        workflow["updated_date"] = datetime.now().isoformat()
        
        # Update in database
        await db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": workflow}
        )
        
        # Broadcast update
        await manager.broadcast({
            "type": "workflow_updated",
            "data": clean_mongo_doc(workflow)
        })
        
        print(f"✅ Action processed successfully")
        
        return {
            "message": "Action traitée avec succès",
            "workflow": clean_mongo_doc(workflow)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'action du workflow: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de l'action: {str(e)}"
        )


# Keep the restart_workflow endpoint as is (it's already correct)
# Keep all notification functions as is (they're already correct)
# Add this endpoint to main.py in Module 4 (after the take_workflow_action endpoint)

@app.post("/workflows/{workflow_id}/restart")
async def restart_workflow(workflow_id: str):
    """Restart workflow after changes are made"""
    try:
        workflow = await db.workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable")
        
        if workflow["overall_status"] not in [ApprovalStatus.CHANGES_REQUESTED, "changes_requested"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Le workflow doit être en état 'Modifications demandées'. État actuel: {workflow['overall_status']}"
            )
        
        # Reset ALL steps back to pending
        for i, step in enumerate(workflow["steps"]):
            step["status"] = ApprovalStatus.PENDING
            step["action"] = None
            step["action_date"] = None
            if step["status"] != ApprovalStatus.CHANGES_REQUESTED:
                step["comments"] = ""
        
        # Start from step 0
        workflow["current_step"] = 0
        workflow["steps"][0]["status"] = ApprovalStatus.IN_PROGRESS
        workflow["overall_status"] = ApprovalStatus.IN_PROGRESS
        workflow["updated_date"] = datetime.now().isoformat()
        
        # Update in database
        await db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": workflow}
        )
        
        # Broadcast update
        await manager.broadcast({
            "type": "workflow_updated",
            "data": clean_mongo_doc(workflow)
        })
        
        print(f"🔄 Workflow {workflow_id} redémarré après modifications")
        
        return {
            "message": "Workflow redémarré avec succès",
            "workflow": clean_mongo_doc(workflow)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors du redémarrage du workflow: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
async def notify_po_service_changes_requested(document_id: str, workflow_id: str, comments: str):
    """Notifier le Module 3 que des modifications sont demandées - REMETTRE EN BROUILLON"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "workflow_id": workflow_id,
                "status": "draft",  # Important: draft status
                "comments": f"Modifications demandées: {comments}"
            }
            
            response = await client.post(
                f"{PO_SERVICE_URL}/bons-commande/{document_id}/approval-callback",
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ Service BC notifié: {document_id} → Brouillon")
            else:
                print(f"⚠️ Échec notification: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️ Connexion BC impossible: {e}")

# Fonction de notification pour l'approbation - NOUVELLE
async def notify_po_service_approved(document_id: str, workflow_id: str):
    """Notifier le Module 3 que le bon de commande est APPROUVÉ"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "workflow_id": workflow_id,
                "status": "approved"
            }
            
            response = await client.post(
                f"{PO_SERVICE_URL}/bons-commande/{document_id}/approval-callback",
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ Service BC notifié: {document_id} → Approuvé")
            else:
                print(f"⚠️ Échec de notification du service BC: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️ Impossible de se connecter au service BC: {e}")

# Fonction de notification pour le rejet - NOUVELLE
async def notify_po_service_rejected(document_id: str, workflow_id: str, comments: str):
    """Notifier le Module 3 que le bon de commande est REJETÉ"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "workflow_id": workflow_id,
                "status": "rejected",
                "comments": comments
            }
            
            response = await client.post(
                f"{PO_SERVICE_URL}/bons-commande/{document_id}/approval-callback",
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ Service BC notifié: {document_id} → Rejeté")
            else:
                print(f"⚠️ Échec de notification du service BC: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️ Impossible de se connecter au service BC: {e}")

@app.post("/workflows/{workflow_id}/comments")
async def add_comment(workflow_id: str, comment: Comment):
    """Ajouter un commentaire au workflow"""
    try:
        workflow = await db.workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable")
        
        comment.comment_id = f"comment_{uuid.uuid4().hex[:8]}"
        comment_dict = comment.dict()
        
        result = await db.workflow_comments.insert_one(comment_dict)
        cleaned_comment = clean_mongo_doc(comment_dict)
        
        await manager.broadcast({
            "type": "comment_added",
            "workflow_id": workflow_id,
            "data": cleaned_comment
        })
        
        print(f"✅ Commentaire ajouté au workflow {workflow_id}")
        
        return {
            "message": "Commentaire ajouté avec succès",
            "comment": cleaned_comment
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du commentaire: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'ajout du commentaire: {str(e)}"
        )

@app.get("/workflows/{workflow_id}/comments")
async def get_comments(workflow_id: str):
    """Obtenir tous les commentaires d'un workflow"""
    try:
        comments = []
        async for comment in db.workflow_comments.find({"workflow_id": workflow_id}):
            comments.append(clean_mongo_doc(comment))
        
        return comments
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention des commentaires: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/{workflow_id}/progress")
async def get_workflow_progress(workflow_id: str):
    """Obtenir l'analyse de progression du workflow"""
    try:
        workflow = await db.workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable")
        
        total_steps = len(workflow["steps"])
        completed_steps = sum(1 for step in workflow["steps"] if step["status"] == ApprovalStatus.APPROVED)
        pending_steps = sum(1 for step in workflow["steps"] if step["status"] in [ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS])
        
        progress_percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "pending_steps": pending_steps,
            "progress_percentage": progress_percentage,
            "current_status": workflow["overall_status"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention de la progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
async def get_users():
    """Obtenir tous les utilisateurs (pour la délégation)"""
    return MOCK_USERS



    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)