from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from uuid import uuid4
from datetime import datetime
from typing import Optional, List
import secrets
import base64
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.models import PR, TypeAchat, StatutPR, Document, PRResponse
    from backend.db import get_pr_collection
    from backend.email_service import send_validation_email, send_notification_email
except ImportError:
    # Fallback for different import styles
    from models import PR, TypeAchat, StatutPR, Document, PRResponse
    from db import get_pr_collection
    from email_service import send_validation_email, send_notification_email

app = FastAPI(title="ERP Achat - PR Management")

print("="*50)
print("🚀 FastAPI Application Starting...")
print("="*50)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pr_collection = get_pr_collection()

# ---------- CREATE PR ----------
@app.post("/pr/", response_model=dict)
async def create_pr(
    demandeur: str = Form(...),
    email_demandeur: str = Form(...),
    manager_email: str = Form(...),
    finance_email: str = Form(...),
    type_achat: str = Form(...),
    details: str = Form(...),
    quantite: Optional[int] = Form(None),
    unite: Optional[str] = Form(None),
    prix_estime: Optional[float] = Form(None),
    fournisseur_suggere: Optional[str] = Form(None),
    centre_cout: Optional[str] = Form(None),
    priorite: str = Form("Moyenne"),
    delai_souhaite: Optional[str] = Form(None),
    justification: Optional[str] = Form(None),
    specifications_techniques: Optional[str] = Form(None),
    description_service: Optional[str] = Form(None),
    duree_contrat: Optional[str] = Form(None),
    reference_catalogue: Optional[str] = Form(None),
    files: List[UploadFile] = File(None)
):
    pr_id = str(uuid4())[:8]
    validation_token = secrets.token_urlsafe(32)
    
    # Process documents
    documents = []
    if files:
        for f in files:
            content = await f.read()
            documents.append({
                "filename": f.filename,
                "content_type": f.content_type,
                "data": base64.b64encode(content).decode('utf-8')
            })
    
    # Create PR document
    pr_doc = {
        "id": pr_id,
        "demandeur": demandeur,
        "email_demandeur": email_demandeur,
        "manager_email": manager_email,
        "finance_email": finance_email,
        "type_achat": type_achat,
        "details": details,
        "quantite": quantite,
        "unite": unite,
        "prix_estime": prix_estime,
        "fournisseur_suggere": fournisseur_suggere,
        "centre_cout": centre_cout,
        "priorite": priorite,
        "delai_souhaite": delai_souhaite,
        "justification": justification,
        "specifications_techniques": specifications_techniques,
        "description_service": description_service,
        "duree_contrat": duree_contrat,
        "reference_catalogue": reference_catalogue,
        "statut": StatutPR.BROUILLON.value,
        "date_creation": datetime.now().isoformat(),
        "history": [{
            "action": "Création",
            "user": demandeur,
            "timestamp": datetime.now().isoformat(),
            "statut": StatutPR.BROUILLON.value
        }],
        "documents": documents,
        "validation_token": validation_token
    }
    
    # Save to MongoDB
    pr_collection.insert_one(pr_doc)
    
    print(f"✓ PR {pr_id} créée par {demandeur}")
    
    return {
        "message": "PR créée avec succès",
        "pr_id": pr_id,
        "statut": StatutPR.BROUILLON.value
    }

# ---------- SUBMIT PR FOR VALIDATION ----------
@app.post("/pr/{pr_id}/submit")
async def submit_pr(pr_id: str):
    pr = pr_collection.find_one({"id": pr_id})
    if not pr:
        raise HTTPException(status_code=404, detail="PR non trouvée")
    
    if pr["statut"] != StatutPR.BROUILLON.value:
        raise HTTPException(status_code=400, detail="PR déjà soumise")
    
    # Update status
    pr_collection.update_one(
        {"id": pr_id},
        {
            "$set": {"statut": StatutPR.EN_VALIDATION_HIERARCHIQUE.value},
            "$push": {
                "history": {
                    "action": "Soumission pour validation hiérarchique",
                    "user": pr["demandeur"],
                    "timestamp": datetime.now().isoformat(),
                    "statut": StatutPR.EN_VALIDATION_HIERARCHIQUE.value
                }
            }
        }
    )
    
    # Send email to manager
    send_validation_email(
        to_email=pr["manager_email"],
        pr_id=pr_id,
        pr_details=pr,
        validation_type="hierarchique",
        token=pr["validation_token"]
    )
    
    print(f"✓ PR {pr_id} soumise pour validation hiérarchique")
    
    return {
        "message": "PR soumise pour validation hiérarchique",
        "statut": StatutPR.EN_VALIDATION_HIERARCHIQUE.value
    }

# ---------- VALIDATION ENDPOINT (from email) ----------
@app.get("/pr/{pr_id}/validate")
async def validate_pr(
    pr_id: str,
    token: str = Query(...),
    action: str = Query(...),  # approve or reject
    type: str = Query(...)  # hierarchique or budgetaire
):
    pr = pr_collection.find_one({"id": pr_id})
    if not pr:
        return HTMLResponse("<h2>❌ PR non trouvée</h2>")
    
    if pr["validation_token"] != token:
        return HTMLResponse("<h2>❌ Token invalide</h2>")
    
    approved = action == "approve"
    
    if type == "hierarchique":
        if pr["statut"] != StatutPR.EN_VALIDATION_HIERARCHIQUE.value:
            return HTMLResponse("<h2>⚠️ Cette PR n'est pas en attente de validation hiérarchique</h2>")
        
        if approved:
            new_status = StatutPR.VALIDEE.value
            message = "approuvée par le manager"
            
            # Update status
            pr_collection.update_one(
                {"id": pr_id},
                {
                    "$set": {"statut": new_status},
                    "$push": {
                        "history": {
                            "action": "Validation hiérarchique",
                            "user": pr["manager_email"],
                            "approved": True,
                            "timestamp": datetime.now().isoformat(),
                            "statut": new_status
                        }
                    }
                }
            )
            
            # Send email to finance
            send_validation_email(
                to_email=pr["finance_email"],
                pr_id=pr_id,
                pr_details=pr,
                validation_type="budgetaire",
                token=pr["validation_token"]
            )
            
            # Notify requester
            send_notification_email(
                to_email=pr["email_demandeur"],
                subject=f"PR {pr_id} validée hiérarchiquement",
                message=f"Votre PR {pr_id} a été approuvée par votre manager et est maintenant en attente de validation budgétaire."
            )
            
            return HTMLResponse(f"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #10b981;">✓ PR {pr_id} Approuvée</h1>
                    <p>La PR a été validée hiérarchiquement et envoyée au service financier.</p>
                </body></html>
            """)
        else:
            new_status = StatutPR.REJETEE.value
            pr_collection.update_one(
                {"id": pr_id},
                {
                    "$set": {"statut": new_status},
                    "$push": {
                        "history": {
                            "action": "Rejet hiérarchique",
                            "user": pr["manager_email"],
                            "approved": False,
                            "timestamp": datetime.now().isoformat(),
                            "statut": new_status
                        }
                    }
                }
            )
            
            send_notification_email(
                to_email=pr["email_demandeur"],
                subject=f"PR {pr_id} rejetée",
                message=f"Votre PR {pr_id} a été rejetée par votre manager."
            )
            
            return HTMLResponse(f"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #ef4444;">✗ PR {pr_id} Rejetée</h1>
                    <p>La PR a été rejetée au niveau hiérarchique.</p>
                </body></html>
            """)
    
    elif type == "budgetaire":
        if pr["statut"] != StatutPR.VALIDEE.value:
            return HTMLResponse("<h2>⚠️ Cette PR n'est pas en attente de validation budgétaire</h2>")
        
        if approved:
            new_status = StatutPR.ACTIVE.value
            
            pr_collection.update_one(
                {"id": pr_id},
                {
                    "$set": {"statut": new_status},
                    "$push": {
                        "history": {
                            "action": "Validation budgétaire",
                            "user": pr["finance_email"],
                            "approved": True,
                            "timestamp": datetime.now().isoformat(),
                            "statut": new_status
                        }
                    }
                }
            )
            
            send_notification_email(
                to_email=pr["email_demandeur"],
                subject=f"PR {pr_id} approuvée - ACTIVE",
                message=f"Votre PR {pr_id} a été approuvée par le service financier. Elle est maintenant active et peut être convertie en PO."
            )
            
            return HTMLResponse(f"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #10b981;">✓ PR {pr_id} Active</h1>
                    <p>La PR a été validée budgétairement et est maintenant ACTIVE.</p>
                </body></html>
            """)
        else:
            new_status = StatutPR.REJETEE.value
            
            pr_collection.update_one(
                {"id": pr_id},
                {
                    "$set": {"statut": new_status},
                    "$push": {
                        "history": {
                            "action": "Rejet budgétaire",
                            "user": pr["finance_email"],
                            "approved": False,
                            "timestamp": datetime.now().isoformat(),
                            "statut": new_status
                        }
                    }
                }
            )
            
            send_notification_email(
                to_email=pr["email_demandeur"],
                subject=f"PR {pr_id} rejetée",
                message=f"Votre PR {pr_id} a été rejetée par le service financier (budget insuffisant)."
            )
            
            return HTMLResponse(f"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #ef4444;">✗ PR {pr_id} Rejetée</h1>
                    <p>La PR a été rejetée au niveau budgétaire.</p>
                </body></html>
            """)

# ---------- LIST PRs ----------
@app.get("/pr/", response_model=List[dict])
def list_prs(statut: Optional[str] = None):
    query = {}
    if statut:
        query["statut"] = statut
    
    prs = list(pr_collection.find(query, {"_id": 0, "validation_token": 0, "documents.data": 0}))
    return prs

# ---------- GET PR DETAILS ----------
@app.get("/pr/{pr_id}")
def get_pr(pr_id: str):
    pr = pr_collection.find_one({"id": pr_id}, {"_id": 0, "validation_token": 0})
    if not pr:
        raise HTTPException(status_code=404, detail="PR non trouvée")
    return pr

# ---------- ARCHIVE PR ----------
@app.post("/pr/{pr_id}/archive")
def archive_pr(pr_id: str, user: str = Form(...)):
    pr = pr_collection.find_one({"id": pr_id})
    if not pr:
        raise HTTPException(status_code=404, detail="PR non trouvée")
    
    pr_collection.update_one(
        {"id": pr_id},
        {
            "$set": {"statut": StatutPR.ARCHIVEE.value},
            "$push": {
                "history": {
                    "action": "Archivage",
                    "user": user,
                    "timestamp": datetime.now().isoformat(),
                    "statut": StatutPR.ARCHIVEE.value
                }
            }
        }
    )
    
    print(f"✓ PR {pr_id} archivée")
    return {"message": f"PR {pr_id} archivée"}

@app.get("/")
def root():
    return {
        "message": "ERP Achat API - PR Management", 
        "version": "1.0",
        "endpoints": {
            "docs": "/docs",
            "create_pr": "POST /pr/",
            "list_pr": "GET /pr/",
            "get_pr": "GET /pr/{pr_id}",
            "submit_pr": "POST /pr/{pr_id}/submit",
            "validate_pr": "GET /pr/{pr_id}/validate",
            "archive_pr": "POST /pr/{pr_id}/archive"
        }
    }

# Startup event to verify everything is loaded
@app.on_event("startup")
async def startup_event():
    print("✅ FastAPI app started successfully")
    print("📝 Available routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"   {list(route.methods)[0]:6} {route.path}")
    print("="*50)