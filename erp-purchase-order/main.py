# main.py
import os
from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from database import connect_to_mongo, close_mongo_connection, get_database
from models import BonCommandeCreate, BonCommandeInDB, StatusUpdate, POCreate
from datetime import date, datetime
from typing import List, Dict
import httpx
import uuid

app = FastAPI(title="SystÃ¨me ERP - Bons de Commande - Module 3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html introuvable")

@app.get("/index.html")
async def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html introuvable")

WORKFLOW_SERVICE_URL = os.getenv("WORKFLOW_SERVICE_URL", "http://localhost:8001")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"âœ… WebSocket connectÃ©. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"âŒ WebSocket dÃ©connectÃ©. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        print(f"ðŸ“¢ Diffusion: {message.get('type')}")
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Ã‰chec d'envoi: {e}")
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

def clean_mongo_doc(doc):
    """Remove MongoDB _id field"""
    if doc and isinstance(doc, dict):
        doc.pop('_id', None)
    return doc

def extraire_departement(email: str) -> str:
    """Extraire le dÃ©partement depuis l'email"""
    if not email:
        return "IT"
    email_lower = email.lower()
    if "finance" in email_lower:
        return "Finance"
    elif "rh" in email_lower or "hr" in email_lower:
        return "RH"
    elif "it" in email_lower or "informatique" in email_lower:
        return "IT"
    elif "achat" in email_lower:
        return "Achats"
    else:
        return "IT"

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    db = await get_database()
    print("âœ… Module 3 connectÃ© Ã  la base de donnÃ©es")

    # Ensure collections exist (no-op if already present)
    collections = await db.list_collection_names()
    if "purchase_orders" not in collections:
        await db.purchase_orders.insert_one({"init": True})
        await db.purchase_orders.delete_one({"init": True})
        print("âœ… Collection 'purchase_orders' crÃ©Ã©e")
    if "purchase_requests" not in collections:
        await db.purchase_requests.insert_one({"init": True})
        await db.purchase_requests.delete_one({"init": True})
        print("âœ… Collection 'purchase_requests' crÃ©Ã©e")
    if "bons_commande" not in collections:
        await db.bons_commande.insert_one({"init": True})
        await db.bons_commande.delete_one({"init": True})
        print("âœ… Collection 'bons_commande' crÃ©Ã©e")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Erreur WS: {e}")
        manager.disconnect(websocket)

# ========== Demandes d'achat (DA) & PR endpoints ==========
@app.get("/demandes-achat")
async def get_demandes_achat():
    db = await get_database()
    das = []
    try:
        async for pr in db.purchase_requests.find({}):
            if "init" in pr:
                continue
            original_status = pr.get("statut", "Active")
            da_formate = {
                "id": pr.get("linked_pr_id", pr.get("id", str(pr.get("_id", "")))),
                "demandeur": pr.get("demandeur", {}).get("nom", "Inconnu") if isinstance(pr.get("demandeur"), dict) else pr.get("demandeur", "Inconnu"),
                "departement": extraire_departement(
                    pr.get("demandeur", {}).get("email", "") if isinstance(pr.get("demandeur"), dict) else pr.get("email_demandeur", "")
                ),
                "type_achat": pr.get("type_achat", "Article"),
                "details": pr.get("details_demande", pr.get("details", "N/A")),
                "date_creation": pr.get("date_creation", str(date.today()))[:10],
                "statut": original_status,
                "email_demandeur": (pr.get("demandeur", {}).get("email", "") if isinstance(pr.get("demandeur"), dict) else pr.get("email_demandeur", "")),
                "manager_email": (pr.get("manager", {}).get("email", "") if isinstance(pr.get("manager"), dict) else pr.get("manager_email", "")),
                "prix_estime": sum(l.get("montant_ligne", 0) for l in pr.get("lignes", [])) if pr.get("lignes") else pr.get("prix_estime", 0),
                "quantite": pr.get("quantite", sum(l.get("quantite", 0) for l in pr.get("lignes", []))),
                "unite": pr.get("unite", "pcs"),
                "fournisseur_suggere": (pr.get("fournisseur", {}).get("nom", "") if isinstance(pr.get("fournisseur"), dict) else pr.get("fournisseur_suggere", "")),
                "priorite": pr.get("priorite", "Haute"),
                "justification": pr.get("justification", "")
            }
            das.append(da_formate)
        print(f"ðŸ“‹ Retour de {len(das)} demandes d'achat au frontend")
        return das
    except Exception as e:
        print(f"âŒ Erreur lors du chargement des DAs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demandes-achat/{da_id}")
async def get_demande_achat(da_id: str):
    db = await get_database()
    try:
        pr = await db.purchase_requests.find_one({"linked_pr_id": da_id}) or await db.purchase_requests.find_one({"id": da_id})
        if not pr:
            raise HTTPException(status_code=404, detail=f"DA {da_id} introuvable")
        formatted_pr = {
            "id": pr.get("linked_pr_id", pr.get("id", str(pr.get("_id", "")))),
            "demandeur": pr.get("demandeur", {}).get("nom", "Inconnu") if isinstance(pr.get("demandeur"), dict) else pr.get("demandeur", "Inconnu"),
            "email_demandeur": pr.get("demandeur", {}).get("email", "") if isinstance(pr.get("demandeur"), dict) else pr.get("email_demandeur", ""),
            "manager_email": pr.get("manager", {}).get("email", "") if isinstance(pr.get("manager"), dict) else pr.get("manager_email", ""),
            "details": pr.get("details_demande", pr.get("details", "N/A")),
            "justification": pr.get("justification", ""),
            "type_achat": pr.get("type_achat", "Produit"),
            "fournisseur_suggere": pr.get("fournisseur", {}).get("nom", "") if isinstance(pr.get("fournisseur"), dict) else pr.get("fournisseur_suggere", ""),
            "statut": pr.get("statut", "Active")
        }
        return formatted_pr
    except HTTPException:
        raise
    except Exception as e:
        print(f"âŒ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bons-commande")
async def get_bons_commande():
    db = await get_database()
    bcs = []
    try:
        async for bc in db.bons_commande.find({}):
            if "init" in bc:
                continue
            bc_clean = clean_mongo_doc(bc)
            bcs.append(bc_clean)
        print(f"ðŸ“¦ Returning {len(bcs)} bons de commande to frontend")
        return bcs
    except Exception as e:
        print(f"âŒ Error loading BCs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== Bons de commande (BC) ==========
@app.post("/bons-commande")
async def create_bon_commande(bc: BonCommandeCreate):
    db = await get_database()
    try:
        # 1) Find the PR
        pr = await db.purchase_requests.find_one(
            {"linked_pr_id": bc.linked_pr_id}
        ) or await db.purchase_requests.find_one({"id": bc.linked_pr_id})

        if not pr:
            raise HTTPException(status_code=404, detail=f"DA {bc.linked_pr_id} introuvable")

        # 2) Generate BC ID
        count = await db.bons_commande.count_documents({})
        bc_id = f"BC-{count + 1:04d}"

        # 3) Calculate totals
        montant_total_ht = sum(l.montant_ligne for l in bc.lignes)
        montant_tva = round(montant_total_ht * 0.19, 3)
        montant_total_ttc = round(montant_total_ht + montant_tva, 3)

        # 4) Extract requester info safely
        demandeur_nom = (bc.demandeur or {}).get("nom", "SystÃ¨me")
        demandeur_email = (bc.demandeur or {}).get("email", "system@erp.com")

        fournisseur_nom = (bc.fournisseur or {}).get("nom", "N/A")

        # 5) Build BC document
        bc_dict = bc.dict()
        bc_dict.update({
            "purchase_order_id": bc_id,
            "montant_total_ht": montant_total_ht,
            "montant_tva": montant_tva,
            "montant_total_ttc": montant_total_ttc,
            "status": "Brouillon",
            "date_creation": datetime.now().isoformat(),
            "history": [{
                "date": datetime.now().isoformat(),
                "action": "CrÃ©ation du BC",
                "utilisateur": demandeur_nom,
                "details": f"BC crÃ©Ã© avec {len(bc.lignes)} ligne(s)"
            }],
            "documents": [],
            "workflow_id": None
        })

        # 6) Insert into DB
        await db.bons_commande.insert_one(bc_dict)

        # 7) Update PR status
        await db.purchase_requests.update_one(
            {"$or": [{"linked_pr_id": bc.linked_pr_id}, {"id": bc.linked_pr_id}]},
            {
                "$set": {"statut": "Convertie en BC"},
                "$push": {"history": {
                    "action": "Conversion en BC",
                    "user": demandeur_nom,
                    "timestamp": datetime.now().isoformat(),
                    "statut": "Convertie en BC",
                    "bc_id": bc_id
                }}
            }
        )

        # 8) Workflow creation - safe mode
        workflow_cree = False
        try:
            async with httpx.AsyncClient() as client:
                workflow_payload = {
                    "document_type": "purchase_order",
                    "document_id": bc_id,
                    "document_title": f"BC {bc_id} - {fournisseur_nom}",
                    "initiator": demandeur_email,
                    "initiator_name": demandeur_nom,
                    "department": extraire_departement(demandeur_email),
                    "total_amount": montant_total_ttc
                }
                response = await client.post(
                    f"{WORKFLOW_SERVICE_URL}/workflows",
                    json=workflow_payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    workflow_data = response.json()
                    workflow_id = workflow_data.get("workflow_id")
                    await db.bons_commande.update_one(
                        {"purchase_order_id": bc_id},
                        {"$set": {"workflow_id": workflow_id, "status": "En attente d'approbation"}}
                    )
                    bc_dict["workflow_id"] = workflow_id
                    bc_dict["status"] = "En attente d'approbation"
                    workflow_cree = True

        except Exception as e:
            print(f"âš ï¸ Workflow service unreachable: {e}")

        bc_dict = clean_mongo_doc(bc_dict)

        # 9) Websocket broadcast
        await manager.broadcast({
            "type": "bc_cree",
            "data": bc_dict,
            "workflow_cree": workflow_cree
        })

        print(f"âœ… BC {bc_id} crÃ©Ã© avec succÃ¨s")
        return bc_dict

    except Exception as e:
        print(f"âŒ Erreur lors de la crÃ©ation du BC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/bons-commande/{bc_id}/statut")
async def update_bc_status(bc_id: str, mise_a_jour: StatusUpdate):
    db = await get_database()
    statuts_valides = ["Brouillon", "En attente d'approbation", "ApprouvÃ©", "RejetÃ©", "Ã‰mis", "ConfirmÃ©", "LivrÃ© partiellement", "LivrÃ© totalement", "Anomalie", "ClÃ´turÃ©"]
    if mise_a_jour.status not in statuts_valides:
        raise HTTPException(status_code=400, detail="Statut invalide")
    result = await db.bons_commande.update_one({"purchase_order_id": bc_id},
        {"$set": {"status": mise_a_jour.status}, "$push": {"history": {"date": datetime.now().isoformat(), "action": f"Changement de statut vers {mise_a_jour.status}", "utilisateur": "SystÃ¨me", "details": mise_a_jour.commentaire or ""}}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="BC introuvable")
    bc = await db.bons_commande.find_one({"purchase_order_id": bc_id})
    bc = clean_mongo_doc(bc)
    await manager.broadcast({"type": "bc_mis_a_jour", "data": bc})
    return {"message": "Statut du BC mis Ã  jour", "nouveau_statut": mise_a_jour.status}


# ========== PR / PO endpoints compatible with frontend ==========
@app.get("/prs")
async def get_prs():
    db = await get_database()
    prs = []
    try:
        async for pr in db.purchase_requests.find({}):
            if "init" in pr:
                continue
            formatted_pr = {
                "id": pr.get("linked_pr_id", pr.get("id", str(pr.get("_id", "")))),
                "requester": pr.get("demandeur", {}).get("nom", "Inconnu") if isinstance(pr.get("demandeur"), dict) else pr.get("demandeur", "Inconnu"),
                "department": extraire_departement(pr.get("demandeur", {}).get("email", "") if isinstance(pr.get("demandeur"), dict) else pr.get("email_demandeur", "")),
                "items": pr.get("details_demande", pr.get("details", "N/A")),
                "date": pr.get("date_creation", str(date.today()))[:10],
                "status": pr.get("statut", "Brouillon")
            }
            prs.append(formatted_pr)
        return prs
    except Exception as e:
        print(f"âŒ Error loading PRs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pos")
async def create_po(po_data: POCreate):
    """Create a purchase order (validated by Pydantic POCreate)"""
    db = await get_database()
    try:
        count = await db.purchase_orders.count_documents({})
        po_id = f"PO-{count + 1:04d}"
        amount = round(po_data.quantity * po_data.unitPrice * (1 + po_data.tax / 100), 2)
        po_doc = {
            "id": po_id,
            "prId": po_data.prId,
            "items": po_data.items,
            "quantity": po_data.quantity,
            "unitPrice": po_data.unitPrice,
            "tax": po_data.tax,
            "amount": amount,
            "supplier": po_data.supplier,
            "delivery": po_data.delivery,
            "status": "Brouillon",
            "date": datetime.now().isoformat(),
            "workflow_id": None
        }
        await db.purchase_orders.insert_one(po_doc)
        # try to create workflow (best-effort)
        try:
            async with httpx.AsyncClient() as client:
                workflow_payload = {
                    "document_type": "purchase_order",
                    "document_id": po_id,
                    "document_title": f"PO {po_id} - {po_data.items}",
                    "initiator": "system@erp.com",
                    "initiator_name": "SystÃ¨me",
                    "department": "Achats",
                    "total_amount": amount
                }
                response = await client.post(f"{WORKFLOW_SERVICE_URL}/workflows", json=workflow_payload, timeout=10.0)
                if response.status_code == 200:
                    workflow_id = response.json().get("workflow_id")
                    await db.purchase_orders.update_one({"id": po_id}, {"$set": {"workflow_id": workflow_id, "status": "En cours d'approbation"}})
                    po_doc["workflow_id"] = workflow_id
                    po_doc["status"] = "En cours d'approbation"
        except Exception as e:
            print(f"âš ï¸ Could not create workflow: {e}")
        po_doc_clean = clean_mongo_doc(po_doc)
        await manager.broadcast({"type": "po_created", "data": po_doc_clean})
        return po_doc_clean
    except Exception as e:
        print(f"âŒ Error creating PO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pos")
async def get_pos():
    db = await get_database()
    pos = []
    try:
        # First get from bons_commande (primary source)
        async for bc in db.bons_commande.find({}):
            if "init" in bc:
                continue
            # Transform BC format to PO format for frontend compatibility
            po_formatted = {
                "id": bc.get("purchase_order_id", bc.get("id", str(bc.get("_id", "")))),
                "prId": bc.get("linked_pr_id", "N/A"),
                "supplier": bc.get("fournisseur", {}).get("nom", "N/A") if isinstance(bc.get("fournisseur"), dict) else bc.get("fournisseur", "N/A"),
                "amount": bc.get("montant_total_ttc", 0),
                "date": bc.get("date_creation", str(date.today()))[:10],
                "status": bc.get("status", "Brouillon"),
                "workflow_id": bc.get("workflow_id"),
                "items": bc.get("details_demande", "N/A"),
                "lignes_count": len(bc.get("lignes", []))
            }
            pos.append(po_formatted)
        
        # Also get from purchase_orders collection (for backwards compatibility)
        async for po in db.purchase_orders.find({}):
            if "init" in po:
                continue
            pos.append(clean_mongo_doc(po))
        
        return pos
    except Exception as e:
        print(f"âŒ Error loading POs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/pos/{po_id}/status")
async def update_po_status(po_id: str, status_data: dict):
    db = await get_database()
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    try:
        result = await db.purchase_orders.update_one({"id": po_id}, {"$set": {"status": new_status}})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="PO not found")
        updated_po = await db.purchase_orders.find_one({"id": po_id})
        updated_po = clean_mongo_doc(updated_po)
        await manager.broadcast({"type": "po_updated", "data": updated_po})
        return {"message": "Status updated successfully", "po": updated_po}
    except Exception as e:
        print(f"âŒ Error updating PO status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    db = await get_database()
    try:
        pr_count = await db.purchase_requests.count_documents({})
        po_count = await db.purchase_orders.count_documents({})
        bc_count = await db.bons_commande.count_documents({})
        # subtract possible init docs (best-effort)
        if await db.purchase_requests.find_one({"init": True}):
            pr_count -= 1
        if await db.purchase_orders.find_one({"init": True}):
            po_count -= 1
        return {"purchase_requests": pr_count, "purchase_orders": po_count, "bons_commande": bc_count}
    except Exception as e:
        print(f"âŒ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add this new endpoint after the approval_callback endpoint (around line 250)






@app.put("/bons-commande/{bc_id}")
async def update_bon_commande(bc_id: str, updates: dict):
    """Update BC details (when changes are requested)"""
    db = await get_database()
    try:
        bc = await db.bons_commande.find_one({"purchase_order_id": bc_id})
        if not bc:
            raise HTTPException(status_code=404, detail="BC introuvable")
        
        # Only allow updates if BC is in Brouillon status
        if bc.get("status") != "Brouillon":
            raise HTTPException(
                status_code=400,
                detail="Seuls les BC en brouillon peuvent Ãªtre modifiÃ©s"
            )
        
        # Update allowed fields
        allowed_fields = [
            "details_demande", "justification", "lignes", "fournisseur",
            "priorite", "date_livraison_souhaitee", "mode_paiement",
            "remarques", "conditions_livraison"
        ]
        
        update_data = {k: v for k, v in updates.items() if k in allowed_fields}
        
        # Recalculate totals if lignes changed
        if "lignes" in update_data:
            montant_total_ht = sum(l.get("montant_ligne", 0) for l in update_data["lignes"])
            montant_tva = round(montant_total_ht * 0.19, 3)
            montant_total_ttc = round(montant_total_ht + montant_tva, 3)
            
            update_data["montant_total_ht"] = montant_total_ht
            update_data["montant_tva"] = montant_tva
            update_data["montant_total_ttc"] = montant_total_ttc
        
        # Add history entry
        history_entry = {
            "date": datetime.now().isoformat(),
            "action": "BC modifiÃ© aprÃ¨s demande de changements",
            "utilisateur": bc.get("demandeur", {}).get("nom", "SystÃ¨me"),
            "details": f"Champs modifiÃ©s: {', '.join(update_data.keys())}"
        }
        
        # Update in database
        result = await db.bons_commande.update_one(
            {"purchase_order_id": bc_id},
            {
                "$set": update_data,
                "$push": {"history": history_entry}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Aucune modification effectuÃ©e")
        
        # Get updated BC
        bc_updated = await db.bons_commande.find_one({"purchase_order_id": bc_id})
        bc_updated = clean_mongo_doc(bc_updated)
        
        # Broadcast update
        await manager.broadcast({
            "type": "bc_mis_a_jour",
            "data": bc_updated
        })
        
        print(f"âœ… BC {bc_id} mis Ã  jour")
        
        return {
            "message": "BC mis Ã  jour avec succÃ¨s",
            "bc": bc_updated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"âŒ Erreur lors de la mise Ã  jour du BC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CRITICAL FIXES FOR MODULE 3 (main.py)
# Replace the approval_callback endpoint with this corrected version:

@app.post("/bons-commande/{bc_id}/approval-callback")
async def approval_callback(bc_id: str, statut_workflow: dict):
    """
    Handle workflow status updates from Module 4
    FIXED: Proper PR status management for changes_requested flow
    """
    db = await get_database()
    bc = await db.bons_commande.find_one({"purchase_order_id": bc_id})
    if not bc:
        raise HTTPException(status_code=404, detail="BC introuvable")
    
    nouveau_statut = None
    etat_workflow = statut_workflow.get("status")
    comments = statut_workflow.get("comments", "")
    pr_id = bc.get("linked_pr_id")
    
    print(f"📥 Callback received for BC {bc_id}: workflow status = {etat_workflow}")
    
    # Handle different workflow statuses
    if etat_workflow == "completed" or etat_workflow == "approved":
        nouveau_statut = "Approuvé"
        
        # Keep PR as "Convertie en BC" when approved
        if pr_id:
            await db.purchase_requests.update_one(
                {"$or": [{"linked_pr_id": pr_id}, {"id": pr_id}]},
                {
                    "$set": {"statut": "Convertie en BC"},
                    "$push": {
                        "history": {
                            "action": "BC approuvé",
                            "user": "Système",
                            "timestamp": datetime.now().isoformat(),
                            "statut": "Convertie en BC",
                            "bc_id": bc_id
                        }
                    }
                }
            )
            print(f"✅ PR {pr_id} kept as 'Convertie en BC' (BC approved)")
    
    elif etat_workflow == "rejected":
        nouveau_statut = "Rejeté"
        
        # Set PR back to Active when BC is rejected
        if pr_id:
            await db.purchase_requests.update_one(
                {"$or": [{"linked_pr_id": pr_id}, {"id": pr_id}]},
                {
                    "$set": {"statut": "Active"},
                    "$push": {
                        "history": {
                            "action": "BC rejeté - PR réactivée",
                            "user": "Système",
                            "timestamp": datetime.now().isoformat(),
                            "statut": "Active",
                            "details": f"BC {bc_id} rejeté: {comments}"
                        }
                    }
                }
            )
            print(f"✅ PR {pr_id} set back to Active (BC rejected)")
    
    elif etat_workflow == "draft":
        # Changes requested - put BC in Brouillon and PR back to Active
        nouveau_statut = "Brouillon"
        
        if pr_id:
            await db.purchase_requests.update_one(
                {"$or": [{"linked_pr_id": pr_id}, {"id": pr_id}]},
                {
                    "$set": {"statut": "Active"},
                    "$push": {
                        "history": {
                            "action": "Modifications demandées - PR réactivée",
                            "user": "Système",
                            "timestamp": datetime.now().isoformat(),
                            "statut": "Active",
                            "details": f"Modifications demandées sur BC {bc_id}: {comments}"
                        }
                    }
                }
            )
            print(f"✅ PR {pr_id} reactivated (changes requested on BC)")
            
            # Broadcast PR reactivation
            updated_pr = await db.purchase_requests.find_one(
                {"$or": [{"linked_pr_id": pr_id}, {"id": pr_id}]}
            )
            if updated_pr:
                await manager.broadcast({
                    "type": "pr_updated",
                    "data": clean_mongo_doc(updated_pr)
                })
    
    # Update BC status
    if nouveau_statut:
        await db.bons_commande.update_one(
            {"purchase_order_id": bc_id},
            {
                "$set": {"status": nouveau_statut},
                "$push": {
                    "history": {
                        "date": datetime.now().isoformat(),
                        "action": f"Workflow terminé - {nouveau_statut}",
                        "utilisateur": "Système",
                        "details": f"Workflow ID: {bc.get('workflow_id')}. {comments}"
                    }
                }
            }
        )
        
        bc_mis_a_jour = await db.bons_commande.find_one({"purchase_order_id": bc_id})
        bc_mis_a_jour = clean_mongo_doc(bc_mis_a_jour)
        
        await manager.broadcast({
            "type": "bc_mis_a_jour",
            "data": bc_mis_a_jour
        })
        
        print(f"✅ BC {bc_id} status updated to: {nouveau_statut}")
    
    return {"message": f"Statut du BC mis à jour: {nouveau_statut}"}


# ALSO UPDATE the resubmit_bon_commande endpoint:

@app.post("/bons-commande/{bc_id}/resubmit")
async def resubmit_bon_commande(bc_id: str):
    """
    Resubmit BC for approval after changes requested
    FIXED: Properly set PR back to "Convertie en BC"
    """
    db = await get_database()
    try:
        bc = await db.bons_commande.find_one({"purchase_order_id": bc_id})
        if not bc:
            raise HTTPException(status_code=404, detail="BC introuvable")
        
        if bc.get("status") != "Brouillon":
            raise HTTPException(
                status_code=400, 
                detail=f"Le BC doit être en statut 'Brouillon'. Statut actuel: {bc.get('status')}"
            )
        
        workflow_id = bc.get("workflow_id")
        if not workflow_id:
            raise HTTPException(status_code=400, detail="Aucun workflow associé")
        
        # 1️⃣ FIRST: Set PR back to "Convertie en BC"
        pr_id = bc.get("linked_pr_id")
        if pr_id:
            pr_result = await db.purchase_requests.update_one(
                {"$or": [{"linked_pr_id": pr_id}, {"id": pr_id}]},
                {
                    "$set": {"statut": "Convertie en BC"},
                    "$push": {
                        "history": {
                            "action": "BC resoumis - PR convertie",
                            "user": bc.get("demandeur", {}).get("nom", "Système"),
                            "timestamp": datetime.now().isoformat(),
                            "statut": "Convertie en BC",
                            "bc_id": bc_id
                        }
                    }
                }
            )
            print(f"✅ PR {pr_id} set back to 'Convertie en BC' (BC resubmitted)")
        
        # 2️⃣ Call Module 4 to restart the workflow
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{WORKFLOW_SERVICE_URL}/workflows/{workflow_id}/restart",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    # 3️⃣ Update BC status to "En attente d'approbation"
                    await db.bons_commande.update_one(
                        {"purchase_order_id": bc_id},
                        {
                            "$set": {"status": "En attente d'approbation"},
                            "$push": {
                                "history": {
                                    "date": datetime.now().isoformat(),
                                    "action": "BC resoumis pour approbation",
                                    "utilisateur": bc.get("demandeur", {}).get("nom", "Système"),
                                    "details": f"Workflow {workflow_id} redémarré"
                                }
                            }
                        }
                    )
                    
                    bc_updated = await db.bons_commande.find_one({"purchase_order_id": bc_id})
                    bc_updated = clean_mongo_doc(bc_updated)
                    
                    # 4️⃣ Broadcast updates
                    await manager.broadcast({
                        "type": "bc_resoumis",
                        "data": bc_updated
                    })
                    
                    # Also broadcast PR update
                    if pr_id:
                        updated_pr = await db.purchase_requests.find_one(
                            {"$or": [{"linked_pr_id": pr_id}, {"id": pr_id}]}
                        )
                        if updated_pr:
                            await manager.broadcast({
                                "type": "pr_updated",
                                "data": clean_mongo_doc(updated_pr)
                            })
                    
                    print(f"✅ BC {bc_id} resubmitted - workflow {workflow_id} restarted")
                    
                    return {
                        "message": "BC resoumis avec succès",
                        "bc": bc_updated
                    }
                else:
                    error_detail = response.text
                    raise HTTPException(
                        status_code=500,
                        detail=f"Échec du redémarrage du workflow: {error_detail}"
                    )
                    
        except httpx.RequestError as e:
            print(f"⚠️ Impossible de se connecter au service workflow: {e}")
            raise HTTPException(
                status_code=503,
                detail="Service de workflow indisponible"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la resoumission du BC: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/bons-commande/{bc_id}")
async def get_bon_commande(bc_id: str):
    """Get a single bon de commande by ID"""
    db = await get_database()
    try:
        bc = await db.bons_commande.find_one({"purchase_order_id": bc_id})
        if not bc:
            raise HTTPException(status_code=404, detail=f"BC {bc_id} introuvable")
        
        bc_clean = clean_mongo_doc(bc)
        return bc_clean
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du BC: {e}")
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))