from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
from uuid import uuid4
import logging
import os
from facture_ocr import FactureOCREasyOCR
from facture_validator import FactureValidator
from db import get_database
from email_service import send_notification_email

logger = logging.getLogger(__name__)

facture_router = APIRouter(prefix="/factures", tags=["Factures"])

# Get MongoDB collections
db = get_database()
po_collection = db["bons_commande"]  # ✅ FIXED: Use correct collection name
facture_collection = db["factures"]

# Initialize EasyOCR (no API key needed!)
try:
    ocr_reader = FactureOCREasyOCR(languages=['fr', 'en'])
    logger.info("✅ EasyOCR initialized and ready")
except Exception as e:
    logger.error(f"❌ Failed to initialize EasyOCR: {e}")
    ocr_reader = None


def map_po_fields(po: dict) -> dict:
    """
    Map bons_commande structure to expected PO structure for validation
    """
    # Extract first ligne if exists
    first_ligne = po.get("lignes", [{}])[0] if po.get("lignes") else {}
    
    # Calculate total quantity from all lines
    total_quantite = sum(ligne.get("quantite", 0) for ligne in po.get("lignes", []))
    
    return {
        "purchase_order_id": po.get("purchase_order_id"),
        "linked_pr_id": po.get("linked_pr_id"),
        "type_achat": po.get("type_achat"),
        "quantite": total_quantite or first_ligne.get("quantite"),
        "unite": first_ligne.get("unite"),
        "prix_estime": po.get("montant_total_ttc"),
        "montant_ht": po.get("montant_total_ht"),
        "montant_tva": po.get("montant_tva"),
        "montant_ttc": po.get("montant_total_ttc"),
        "devise": po.get("devise", "TND"),
        "centre_cout": po.get("centre_cout"),
        "priorite": po.get("priorite"),
        "delai_souhaite": po.get("delai_souhaite"),
        "date_livraison_souhaitee": po.get("date_livraison_souhaitee"),
        "specifications_techniques": first_ligne.get("specifications_techniques") or first_ligne.get("description"),
        "fournisseur": po.get("fournisseur", {}),
        "demandeur": po.get("demandeur", {}),
        "details": po.get("details_demande"),
        "items": po.get("lignes", [])
    }


@facture_router.post("/upload-and-validate")
async def upload_facture_with_po_validation(
    file: UploadFile = File(...),
    po_id: str = Form(...),
    user_email: str = Form(...)
):
    """
    Extraire une facture depuis un fichier uploadé et valider contre un PO
    
    Uses EasyOCR for local, offline text extraction (no API needed!)
    
    Steps:
    1. Read uploaded file bytes
    2. Extract text using EasyOCR (local processing)
    3. Parse extracted data into structured fields
    4. Retrieve PO from database
    5. Validate invoice against PO
    6. Save to MongoDB
    7. Send email notification if errors detected
    8. Return detailed results
    """
    facture_id = None
    try:
        facture_id = f"FACT-{uuid4().hex[:8].upper()}"
        logger.info(f"📤 Traitement facture: {file.filename}")
        logger.info(f"🔗 Liée au PO: {po_id}")

        # Check if OCR is initialized
        if ocr_reader is None:
            raise HTTPException(
                status_code=500,
                detail="EasyOCR not initialized. Please restart the server."
            )

        # Step 1: Read file bytes directly (no upload to external service needed!)
        logger.info("📖 Reading uploaded file...")
        file_bytes = await file.read()
        logger.info(f"✅ File read: {len(file_bytes)} bytes")

        # Step 2: OCR Extraction using EasyOCR
        logger.info("🔍 Starting OCR extraction with EasyOCR...")
        ocr_result = ocr_reader.extract_from_bytes(file_bytes)

        if not ocr_result.get("success"):
            error_msg = f"OCR extraction failed: {ocr_result.get('error')}"
            logger.error(f"❌ {error_msg}")
            
            # Send error email
            send_notification_email(
                to_email=user_email,
                subject=f"❌ Échec d'extraction OCR - Facture {facture_id}",
                message=f"""
                <p>Bonjour,</p>
                <p>L'extraction OCR de votre facture <strong>{file.filename}</strong> a échoué.</p>
                <p><strong>Raison:</strong> {ocr_result.get('error')}</p>
                <p>Veuillez vérifier que:</p>
                <ul>
                    <li>Le fichier est une image ou PDF lisible</li>
                    <li>La qualité de l'image est suffisante</li>
                    <li>Le texte est bien visible et non flou</li>
                    <li>L'orientation de l'image est correcte</li>
                </ul>
                <p>Vous pouvez réessayer avec un fichier de meilleure qualité.</p>
                """,
                pr_id=facture_id
            )
            
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )

        logger.info(f"✅ OCR completed - Confidence: {ocr_result.get('confidence')*100:.1f}%")
        logger.info(f"📊 Extracted {len(ocr_result.get('raw_text', ''))} characters")

        # Step 3: Retrieve PO from database
        logger.info(f"🔍 Searching for PO: {po_id}")
        po_raw = po_collection.find_one({"purchase_order_id": po_id})

        # Try with BC prefix if user entered just the number
        if not po_raw and not po_id.startswith("BC-"):
            logger.info(f"🔍 Trying with BC- prefix: BC-{po_id}")
            po_raw = po_collection.find_one({"purchase_order_id": f"BC-{po_id}"})
            if po_raw:
                po_id = f"BC-{po_id}"  # Update po_id for consistency
        
        if not po_raw:
            error_msg = f"Purchase Order {po_id} not found in bons_commande collection"
            logger.error(f"❌ {error_msg}")
            
            # Send error email
            send_notification_email(
                to_email=user_email,
                subject=f"❌ PO Introuvable - Facture {facture_id}",
                message=f"""
                <p>Bonjour,</p>
                <p>Le bon de commande <strong>{po_id}</strong> est introuvable dans la base de données.</p>
                <p>Veuillez vérifier que:</p>
                <ul>
                    <li>L'ID du PO est correct (format: BC-XXXX ou simplement le numéro)</li>
                    <li>Le PO existe bien dans le système</li>
                    <li>Le PO n'a pas été supprimé</li>
                </ul>
                <p>Fichier uploadé: <strong>{file.filename}</strong></p>
                <p><strong>Données extraites:</strong></p>
                <ul>
                    <li>Numéro facture: {ocr_result.get('numero_facture', 'N/A')}</li>
                    <li>Fournisseur: {ocr_result.get('fournisseur_nom', 'N/A')}</li>
                    <li>Montant: {ocr_result.get('montant_ttc', 'N/A')} {ocr_result.get('devise', 'TND')}</li>
                </ul>
                """,
                pr_id=facture_id
            )
            
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )

        logger.info(f"✅ PO found: {po_raw.get('purchase_order_id')}")
        
        # Map the PO structure to expected format
        po = map_po_fields(po_raw)
        logger.info(f"✅ PO mapped successfully")

        # Step 4: Validation against PO
        logger.info("🔍 Validating invoice against PO...")
        validator = FactureValidator(po_collection)
        validation = validator.validate_against_po(ocr_result, po_id)

        logger.info(f"📊 Validation score: {validation['confidence_score']}%")
        logger.info(f"✅ Matched fields: {len(validation['matched_fields'])}/10")
        logger.info(f"❌ Errors: {len(validation['errors'])}")
        logger.info(f"⚠️  Warnings: {len(validation['warnings'])}")

        # Step 5: Prepare invoice document
        facture_doc = {
            "facture_id": facture_id,
            "linked_po_id": po_id,
            "linked_pr_id": po.get("linked_pr_id", ""),
            
            # OCR extracted data
            "numero_facture": ocr_result.get("numero_facture"),
            "date_facture": ocr_result.get("date_facture"),
            "date_reception": datetime.now().isoformat(),
            
            # Supplier info
            "fournisseur_nom": ocr_result.get("fournisseur_nom") or po.get("fournisseur", {}).get("nom"),
            "fournisseur_matricule": ocr_result.get("fournisseur_matricule"),
            
            # Amounts
            "montant_ht": ocr_result.get("montant_ht"),
            "montant_tva": ocr_result.get("montant_tva"),
            "montant_ttc": ocr_result.get("montant_ttc"),
            "devise": ocr_result.get("devise", "TND"),
            
            # Required fields for comparison
            "type_achat": ocr_result.get("type_achat") or po.get("type_achat"),
            "quantite": ocr_result.get("quantite") or po.get("quantite"),
            "unite": ocr_result.get("unite") or po.get("unite"),
            "centre_cout": po.get("centre_cout"),
            "priorite": po.get("priorite"),
            "delai_souhaite": po.get("delai_souhaite"),
            "date_livraison_souhaite": po.get("date_livraison_souhaitee"),
            "specifications_techniques": ocr_result.get("specifications_techniques") or po.get("specifications_techniques"),
            
            # Status
            "status": "Validée" if validation["is_valid"] else "En attente correction",
            
            # OCR metadata
            "ocr_data": {
                "method": "EasyOCR",
                "confidence": ocr_result.get("confidence", 0.0),
                "raw_text": ocr_result.get("raw_text", "")[:500],
                "extraction_date": datetime.now().isoformat()
            },
            
            # Validation results
            "validation_result": {
                "is_valid": validation["is_valid"],
                "confidence_score": validation["confidence_score"],
                "matched_fields": validation["matched_fields"],
                "mismatches": validation["mismatches"],
                "warnings": validation["warnings"],
                "errors": validation["errors"]
            },
            
            # History
            "history": [{
                "action": "Création via OCR (EasyOCR)",
                "user": user_email,
                "timestamp": datetime.now().isoformat(),
                "status": "Validée" if validation["is_valid"] else "En attente correction",
                "details": f"OCR confidence: {ocr_result.get('confidence', 0)*100:.1f}%"
            }]
        }

        # Step 6: Save to MongoDB
        try:
            logger.info(f"💾 Saving facture to database...")
            facture_collection.insert_one(facture_doc)
            logger.info(f"✅ Facture {facture_id} saved successfully")
        except Exception as db_error:
            logger.error(f"❌ Database save failed: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save facture to database: {str(db_error)}"
            )

        # Step 7: Send email notification if validation failed
        if not validation["is_valid"] or validation["errors"] or validation["warnings"]:
            logger.info("📧 Sending error notification email...")
            email_sent = send_delivery_error_email(
                user_email=user_email,
                facture_id=facture_id,
                po_id=po_id,
                validation_result=validation,
                ocr_data=ocr_result,
                filename=file.filename
            )
            logger.info(f"📧 Email notification sent: {email_sent}")
        else:
            logger.info("✅ Validation passed - No notification email needed")

        # Step 8: Prepare response
        response = {
            "success": True,
            "facture_id": facture_id,
            "linked_po_id": po_id,
            "status": facture_doc["status"],
            
            "ocr_results": {
                "method": "EasyOCR (Local Processing)",
                "confidence": ocr_result.get("confidence", 0.0),
                "extracted_fields": {
                    "numero_facture": ocr_result.get("numero_facture"),
                    "fournisseur": ocr_result.get("fournisseur_nom"),
                    "date_facture": ocr_result.get("date_facture"),
                    "montant_ttc": ocr_result.get("montant_ttc"),
                    "devise": ocr_result.get("devise"),
                    "quantite": ocr_result.get("quantite"),
                    "type_achat": ocr_result.get("type_achat")
                }
            },
            
            "validation_results": validation,
            
            "message": "✅ Facture validée avec succès!" if validation["is_valid"]
                      else "⚠️ Facture nécessite des corrections - Email de notification envoyé"
        }

        logger.info("="*50)
        logger.info(f"✅ FACTURE PROCESSING COMPLETED: {facture_id}")
        logger.info("="*50)

        return JSONResponse(content=response, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Facture processing failed: {str(e)}")
        logger.exception("Full traceback:")
        
        # Send error email for unexpected errors
        if user_email and facture_id:
            send_notification_email(
                to_email=user_email,
                subject=f"❌ Erreur de traitement - Facture {facture_id}",
                message=f"""
                <p>Bonjour,</p>
                <p>Une erreur inattendue s'est produite lors du traitement de votre facture.</p>
                <p><strong>Détails de l'erreur:</strong> {str(e)}</p>
                <p>Fichier uploadé: <strong>{file.filename if file else 'N/A'}</strong></p>
                <p>Veuillez contacter le support technique si le problème persiste.</p>
                """,
                pr_id=facture_id
            )
        
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


def send_delivery_error_email(user_email: str, facture_id: str, po_id: str, 
                               validation_result: dict, ocr_data: dict, filename: str) -> bool:
    """
    Send email notification when delivery errors are detected
    """
    # Build error summary
    errors_html = ""
    if validation_result.get("errors"):
        errors_html = "<h3 style='color:#991b1b;'>❌ Erreurs Critiques:</h3><ul>"
        for error in validation_result["errors"]:
            errors_html += f"<li style='color:#991b1b;'>{error}</li>"
        errors_html += "</ul>"
    
    warnings_html = ""
    if validation_result.get("warnings"):
        warnings_html = "<h3 style='color:#92400e;'>⚠️ Avertissements:</h3><ul>"
        for warning in validation_result["warnings"]:
            warnings_html += f"<li style='color:#92400e;'>{warning}</li>"
        warnings_html += "</ul>"
    
    mismatches_html = ""
    if validation_result.get("mismatches"):
        mismatches_html = "<h3>📊 Différences Détectées:</h3>"
        for mismatch in validation_result["mismatches"]:
            severity_color = "#991b1b" if mismatch.get("severity") == "error" else "#92400e"
            mismatches_html += f"""
            <div style='background-color:#f3f4f6; padding:15px; margin:10px 0; border-left:4px solid {severity_color};'>
                <strong style='color:{severity_color};'>{mismatch.get('field')}:</strong><br>
                <strong>PO:</strong> {mismatch.get('po_value')}<br>
                <strong>Facture:</strong> {mismatch.get('facture_value')}
                {f"<br><strong>Différence:</strong> {mismatch.get('difference')}" if mismatch.get('difference') else ""}
            </div>
            """
    
    message = f"""
    <h2 style='color:#991b1b;'>⚠️ Problème de Livraison Détecté</h2>
    
    <p>Bonjour,</p>
    
    <p>La facture <strong>{filename}</strong> (ID: {facture_id}) a été traitée par notre système d'extraction automatique (EasyOCR) 
    mais des différences ont été détectées par rapport au bon de commande <strong>{po_id}</strong>.</p>
    
    <div style='background-color:#fef3c7; padding:15px; margin:20px 0; border-left:4px solid #f59e0b;'>
        <strong>📊 Résumé de la Validation:</strong><br>
        <strong>Score:</strong> {validation_result.get('confidence_score', 0)}%<br>
        <strong>Champs Validés:</strong> {len(validation_result.get('matched_fields', []))}/10<br>
        <strong>Erreurs Critiques:</strong> {len(validation_result.get('errors', []))}<br>
        <strong>Avertissements:</strong> {len(validation_result.get('warnings', []))}
    </div>
    
    {errors_html}
    {warnings_html}
    {mismatches_html}
    
    <h3>📦 Données Extraites de la Facture (EasyOCR):</h3>
    <div style='background-color:#f9fafb; padding:15px; border-left:4px solid #3b82f6;'>
        <ul style='margin:5px 0;'>
            <li><strong>Numéro Facture:</strong> {ocr_data.get('numero_facture', 'N/A')}</li>
            <li><strong>Fournisseur:</strong> {ocr_data.get('fournisseur_nom', 'N/A')}</li>
            <li><strong>Date:</strong> {ocr_data.get('date_facture', 'N/A')}</li>
            <li><strong>Montant TTC:</strong> {ocr_data.get('montant_ttc', 0)} {ocr_data.get('devise', 'TND')}</li>
            <li><strong>Quantité:</strong> {ocr_data.get('quantite', 'N/A')} {ocr_data.get('unite', '')}</li>
            <li><strong>Type Achat:</strong> {ocr_data.get('type_achat', 'N/A')}</li>
        </ul>
        <p style='margin:10px 0 0 0; font-size:12px; color:#6b7280;'>
            Confiance OCR: {ocr_data.get('confidence', 0)*100:.1f}%
        </p>
    </div>
    
    <div style='background-color:#dbeafe; padding:15px; margin:20px 0; border-left:4px solid #3b82f6;'>
        <strong>ℹ️ Actions Recommandées:</strong>
        <ul>
            <li>✓ Vérifier physiquement les quantités reçues</li>
            <li>✓ Contrôler la conformité des articles livrés</li>
            <li>✓ Vérifier les montants avec la facture papier</li>
            <li>✓ Contacter le fournisseur si nécessaire</li>
            <li>✓ Corriger manuellement dans le système si l'OCR a mal lu</li>
        </ul>
    </div>
    
    <p>La facture a été enregistrée avec le statut <strong style='color:#92400e;'>"En attente correction"</strong> 
    et nécessite votre attention avant approbation pour paiement.</p>
    
    <p style='margin-top:30px;'>Cordialement,<br>
    <strong>Système ERP Achat</strong></p>
    """
    
    return send_notification_email(
        to_email=user_email,
        subject=f"⚠️ Erreur de Livraison Détectée - Facture {facture_id} vs PO {po_id}",
        message=message,
        pr_id=facture_id
    )


# ==================== ENDPOINTS BELOW UNCHANGED ====================

@facture_router.get("/")
async def list_factures(
    status: Optional[str] = None,
    po_id: Optional[str] = None
):
    """Liste toutes les factures avec filtres optionnels"""
    query = {}
    
    if status:
        query["status"] = status
    if po_id:
        query["linked_po_id"] = po_id
    
    factures = list(facture_collection.find(
        query,
        {"_id": 0, "ocr_data.raw_text": 0}
    ))
    
    return {"total": len(factures), "factures": factures}


@facture_router.get("/{facture_id}")
async def get_facture_details(facture_id: str):
    """Récupérer les détails d'une facture"""
    facture = facture_collection.find_one(
        {"facture_id": facture_id},
        {"_id": 0}
    )
    
    if not facture:
        raise HTTPException(status_code=404, detail="Facture not found")
    
    return facture


@facture_router.post("/{facture_id}/approve")
async def approve_facture(facture_id: str, user: str = Form(...)):
    """Approuver une facture pour paiement"""
    facture = facture_collection.find_one({"facture_id": facture_id})
    
    if not facture:
        raise HTTPException(status_code=404, detail="Facture not found")
    
    if facture["status"] not in ["Validée", "En attente correction"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve facture with status: {facture['status']}"
        )
    
    facture_collection.update_one(
        {"facture_id": facture_id},
        {
            "$set": {"status": "Approuvée"},
            "$push": {
                "history": {
                    "action": "Approbation",
                    "user": user,
                    "timestamp": datetime.now().isoformat(),
                    "status": "Approuvée"
                }
            }
        }
    )
    
    logger.info(f"✅ Facture {facture_id} approved by {user}")
    
    return {"message": f"Facture {facture_id} approuvée avec succès"}


@facture_router.post("/{facture_id}/reject")
async def reject_facture(
    facture_id: str,
    user: str = Form(...),
    reason: str = Form(...)
):
    """Rejeter une facture"""
    facture = facture_collection.find_one({"facture_id": facture_id})
    
    if not facture:
        raise HTTPException(status_code=404, detail="Facture not found")
    
    facture_collection.update_one(
        {"facture_id": facture_id},
        {
            "$set": {"status": "Rejetée"},
            "$push": {
                "history": {
                    "action": "Rejet",
                    "user": user,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                    "status": "Rejetée"
                }
            }
        }
    )
    
    logger.info(f"❌ Facture {facture_id} rejected by {user}")
    
    return {"message": f"Facture {facture_id} rejetée"}


@facture_router.post("/{facture_id}/mark-paid")
async def mark_facture_paid(facture_id: str, user: str = Form(...)):
    """Marquer une facture comme payée"""
    facture = facture_collection.find_one({"facture_id": facture_id})
    
    if not facture:
        raise HTTPException(status_code=404, detail="Facture not found")
    
    if facture["status"] != "Approuvée":
        raise HTTPException(
            status_code=400,
            detail="Only approved factures can be marked as paid"
        )
    
    facture_collection.update_one(
        {"facture_id": facture_id},
        {
            "$set": {"status": "Payée"},
            "$push": {
                "history": {
                    "action": "Paiement effectué",
                    "user": user,
                    "timestamp": datetime.now().isoformat(),
                    "status": "Payée"
                }
            }
        }
    )
    
    logger.info(f"💰 Facture {facture_id} marked as paid")
    
    return {"message": f"Facture {facture_id} marquée comme payée"}


@facture_router.get("/stats/summary")
async def get_facture_statistics():
    """Statistiques des factures pour le dashboard"""
    total = facture_collection.count_documents({})
    
    stats = {
        "total": total,
        "by_status": {},
        "total_amount": 0.0,
        "average_confidence": 0.0
    }
    
    for status in ["Validée", "En attente correction", "Approuvée", "Rejetée", "Payée"]:
        count = facture_collection.count_documents({"status": status})
        stats["by_status"][status] = count
    
    pipeline = [
        {"$group": {
            "_id": None,
            "total": {"$sum": "$montant_ttc"},
            "avg_confidence": {"$avg": "$ocr_data.confidence"}
        }}
    ]
    
    result = list(facture_collection.aggregate(pipeline))
    if result:
        stats["total_amount"] = round(result[0].get("total", 0.0), 2)
        stats["average_confidence"] = round(result[0].get("avg_confidence", 0.0), 2)
    
    return stats