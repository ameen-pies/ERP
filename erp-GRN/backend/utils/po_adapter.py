"""
Adapter to convert between bons_commande format and internal PO format.
"""
from typing import Any
from uuid import uuid4


def bons_commande_to_internal_po(bons_commande_doc: dict) -> dict:
    """
    Convert a bons_commande document to internal PO format.
    
    Maps:
    - purchase_order_id -> po_number
    - fournisseur.nom -> supplier
    - lignes[].description -> item_name
    - lignes[].quantite -> qty_ordered
    - lignes[].prix_unitaire -> unit_price
    - Adds qty_received (default 0) and status (default "open") to lines
    - Uses numero_ligne as line_id or generates one
    """
    # Extract supplier name
    supplier = ""
    if "fournisseur" in bons_commande_doc and isinstance(bons_commande_doc["fournisseur"], dict):
        supplier = bons_commande_doc["fournisseur"].get("nom", "")
    
    # Convert lines
    internal_lines = []
    for ligne in bons_commande_doc.get("lignes", []):
        # Use numero_ligne as line_id if available, otherwise generate one
        line_id = str(ligne.get("numero_ligne", uuid4()))
        
        internal_line = {
            "line_id": line_id,
            "item_name": ligne.get("description", ""),
            "qty_ordered": ligne.get("quantite", 0),
            "unit_price": ligne.get("prix_unitaire", 0.0),
            "qty_received": ligne.get("qty_received", 0),  # Preserve if exists, default 0
            "status": ligne.get("status", "open"),  # Preserve if exists, default "open"
            # Keep original fields for reference
            "numero_ligne": ligne.get("numero_ligne"),
            "montant_ligne": ligne.get("montant_ligne"),
            "unite": ligne.get("unite"),
            "reference_catalogue": ligne.get("reference_catalogue"),
            "specifications_techniques": ligne.get("specifications_techniques"),
        }
        internal_lines.append(internal_line)
    
    # Determine status based on lines (closed/pending only)
    status = "pending"
    if internal_lines:
        if all(line.get("qty_received", 0) >= line.get("qty_ordered", 0) for line in internal_lines):
            status = "closed"
    
    internal_po = {
        "_id": bons_commande_doc.get("_id"),
        "po_number": bons_commande_doc.get("purchase_order_id", ""),
        "supplier": supplier,
        "status": bons_commande_doc.get("status", status),
        "lines": internal_lines,
        "created_at": bons_commande_doc.get("date_creation"),
        # Keep original fields for reference
        "linked_pr_id": bons_commande_doc.get("linked_pr_id"),
        "details_demande": bons_commande_doc.get("details_demande"),
        "justification": bons_commande_doc.get("justification"),
        "type_achat": bons_commande_doc.get("type_achat"),
        "devise": bons_commande_doc.get("devise"),
        "demandeur": bons_commande_doc.get("demandeur"),
        "manager": bons_commande_doc.get("manager"),
        "fournisseur": bons_commande_doc.get("fournisseur"),
        "montant_total_ht": bons_commande_doc.get("montant_total_ht"),
        "montant_tva": bons_commande_doc.get("montant_tva"),
        "montant_total_ttc": bons_commande_doc.get("montant_total_ttc"),
        "history": bons_commande_doc.get("history", []),
    }
    
    return internal_po


def internal_po_to_bons_commande(internal_po: dict) -> dict:
    """
    Convert internal PO format back to bons_commande format.
    Updates the lignes with qty_received and status.
    """
    # Create a copy but exclude internal-only fields
    bons_commande = {k: v for k, v in internal_po.items() if k not in ["po_number", "supplier", "lines", "created_at"]}
    
    # Convert po_number back to purchase_order_id
    if "po_number" in internal_po:
        bons_commande["purchase_order_id"] = internal_po["po_number"]
    
    # Convert supplier back to fournisseur.nom
    if "supplier" in internal_po:
        supplier_name = internal_po["supplier"]
        # Preserve existing fournisseur structure if it exists
        if "fournisseur" not in bons_commande or not isinstance(bons_commande.get("fournisseur"), dict):
            bons_commande["fournisseur"] = {}
        bons_commande["fournisseur"]["nom"] = supplier_name
        # Preserve other fournisseur fields if they exist
        if "fournisseur" in internal_po and isinstance(internal_po["fournisseur"], dict):
            bons_commande["fournisseur"].update({
                k: v for k, v in internal_po["fournisseur"].items() if k != "nom"
            })
    
    # Convert lines back
    if "lines" in internal_po:
        lignes = []
        for idx, line in enumerate(internal_po["lines"]):
            # Use numero_ligne if available, otherwise use line_id or index+1
            numero_ligne = line.get("numero_ligne")
            if numero_ligne is None:
                # Try to extract from line_id if it's numeric
                line_id = line.get("line_id", "")
                try:
                    numero_ligne = int(line_id) if line_id.isdigit() else idx + 1
                except (ValueError, AttributeError):
                    numero_ligne = idx + 1
            
            ligne = {
                "description": line.get("item_name", ""),
                "quantite": line.get("qty_ordered", 0),
                "prix_unitaire": line.get("unit_price", 0.0),
                "montant_ligne": line.get("montant_ligne", line.get("qty_ordered", 0) * line.get("unit_price", 0.0)),
                "unite": line.get("unite", "unité"),
                "numero_ligne": numero_ligne,
                "reference_catalogue": line.get("reference_catalogue") or "",
                "specifications_techniques": line.get("specifications_techniques"),
                "qty_received": line.get("qty_received", 0),
                "status": line.get("status", "open"),
            }
            lignes.append(ligne)
        bons_commande["lignes"] = lignes
    
    # Update status
    if "status" in internal_po:
        bons_commande["status"] = internal_po["status"]
    
    return bons_commande

