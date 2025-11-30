import logging
from typing import Dict
from difflib import SequenceMatcher

import requests
import os
import json
import re as _re_for_json
from typing import Optional

logger = logging.getLogger(__name__)


class FactureValidator:
    """Validateur pour comparer facture vs Purchase Order"""
    
    def __init__(self, po_collection):
        self.po_collection = po_collection
    

    def _call_llm_compare(self, facture_data: Dict, po: Dict) -> Dict:
        """
            RapidAPI endpoint to compare facture_ocr output vs PO
            Returns a dict with optional keys:
            - 'discrepancies': list of {field, po_value, facture_value, severity, reason}
            - 'action_suggerée': one of 'accepter', 'reviser', 'rejeter'
            - 'confidence': float (0-100)
        """

        RAPIDAPI_URL = os.getenv("RAPIDAPI_URL")
        RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
        RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "")

        if not RAPIDAPI_URL or not RAPIDAPI_KEY:
            logger.debug("⚠️ RapidAPI config missing, skipping LLM compare.")
            return {}

        # Build a strict instruction: return ONLY a JSON object with the schema above.
        system_prompt = (
            "You are an automated invoice vs purchase-order comparer. "
            "Given a PO JSON and an Invoice (facture) JSON, return ONLY a single JSON object "
            "with these keys: 'discrepancies' (array), 'action_suggerée' (accepter, reviser, rejeter), "
            "and 'confidence' (0-100). Each discrepancy must contain: field, po_value, facture_value, severity (error|warning|info), reason. "
            "Do NOT include any extra text outside the JSON object."
        )

        # Provide PO and facture bodies; keep them compact
        payload_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                "Compare these two JSON objects (PO and Invoice). "
                "Return the JSON object as specified.\n\nPO:\n" + json.dumps(po, ensure_ascii=False, default=str) +
                "\n\nInvoice (facture):\n" + json.dumps(facture_data, ensure_ascii=False, default=str)
            )}
        ]

        payload = {
            "messages": payload_messages,
            "web_access": False
        }

        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=30)
        except Exception as e:
            logger.warning(f"⚠️ LLM compare request failed: {e}")
            return {}

        if not resp.ok:
            logger.warning(f"⚠️ LLM compare HTTP {resp.status_code}: {resp.text[:500]}")
            return {}

        # Robust parsing: try common JSON shapes, or extract JSON blob from text
        try:
            data = resp.json()
        except Exception:
            raw = resp.text
            # try to find JSON substring
            m = _re_for_json.search(r'(\{[\s\S]*\})', raw)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    logger.debug("⚠️ Could not parse JSON blob from LLM text response.")
                    return {}
            return {}

        # If valid JSON, try to extract the relevant object
        try:
            # OpenAI-like responses: choices -> message -> content
            if isinstance(data, dict):
                choices = data.get("choices")
                if choices and isinstance(choices, list):
                    first = choices[0]
                    msg = first.get("message") or first.get("text") or first.get("content")
                    content = ""
                    if isinstance(msg, dict):
                        content = msg.get("content") or msg.get("text") or ""
                    elif isinstance(msg, str):
                        content = msg
                    if content:
                        m = _re_for_json.search(r'(\{[\s\S]*\})', content)
                        if m:
                            try:
                                return json.loads(m.group(1))
                            except Exception:
                                pass
                        try:
                            return json.loads(content)
                        except Exception:
                            pass

                # Other shapes: top-level 'output'/'result' fields
                for k in ("output", "response", "result", "data"):
                    if k in data:
                        val = data[k]
                        if isinstance(val, dict):
                            return val
                        if isinstance(val, str):
                            m = _re_for_json.search(r'(\{[\s\S]*\})', val)
                            if m:
                                try:
                                    return json.loads(m.group(1))
                                except Exception:
                                    pass
                            try:
                                return json.loads(val)
                            except Exception:
                                pass

                # If top-level dictionary already contains expected keys, return it
                if any(k in data for k in ("discrepancies", "action_suggerée", "confidence")):
                    return data

        except Exception as e:
            logger.debug(f"🔎 Error interpreting LLM compare response: {e}")

        # Final attempt: dump and search for JSON blob
        try:
            text = json.dumps(data)
            m = _re_for_json.search(r'(\{[\s\S]*\})', text)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
        except Exception:
            pass

        logger.debug("⚠️ LLM compare returned no parseable JSON.")
        return {}


    def validate_against_po(self, facture_data: Dict, po_id: str) -> Dict:
        """
            Compare une facture OCR (facture_data) avec un Bon de Commande (PO) stocké en base.
            Combine : 
                - Vérifications internes (Règles métier)
                - Vérifications assistées par LLM
        """
        print("\n================ DEBUG FACTURE DATA ================")
        for k, v in facture_data.items():
            print(f"{k}: {v}")
        print("====================================================\n")

        # RÉCUPÉRATION DU PO
        po = self.po_collection.find_one({"purchase_order_id": po_id})

        if not po:
            return {
                "is_valid": False,
                "confidence_score": 0.0,
                "matched_fields": [],
                "mismatches": [],
                "warnings": [],
                "errors": [f"❌ Bon de commande '{po_id}' introuvable dans la base."]
            }

        # STRUCTURE INITIALE DU RÉSULTAT
        result = {
            "is_valid": True,
            "confidence_score": 0.0,
            "matched_fields": [],
            "mismatches": [],
            "warnings": [],
            "errors": [],
        }

        # Petit utilitaire interne pour ajouter un mismatch proprement
        def _mismatch(field, po_val, fact_val, severity, reason=None):
            result["mismatches"].append({
                "field": field,
                "po_value": po_val,
                "facture_value": fact_val,
                "severity": severity,
                "reason": reason or ""
            })
            if severity == "error":
                result["errors"].append(f"❌ {field}: PO='{po_val}' vs Facture='{fact_val}'. {reason or ''}")
                result["is_valid"] = False
            elif severity == "warning":
                result["warnings"].append(f"⚠️ {field}: PO='{po_val}' vs Facture='{fact_val}'. {reason or ''}")
            else:
                result["warnings"].append(f"ℹ️ {field}: {reason or ''}")

        # 1) TYPE D’ACHAT
        po_type = (po.get("type_achat") or "").strip().lower()
        fc_type = (facture_data.get("type_achat") or "").strip().lower()
        if po_type and fc_type:
            if po_type == fc_type:
                result["matched_fields"].append("type_achat")
            else:
                _mismatch("Type d'achat", po_type, fc_type, "error")

        # 2) QUANTITÉ
        try:
            po_qty = float(po.get("quantite")) if po.get("quantite") is not None else None
            fc_qty = float(facture_data.get("quantite")) if facture_data.get("quantite") is not None else None

            if po_qty is not None and fc_qty is not None:
                if po_qty == fc_qty:
                    result["matched_fields"].append("quantite")
                else:
                    diff = abs(po_qty - fc_qty)
                    pct = diff / po_qty * 100 if po_qty else 100
                    sev = "error" if pct > 10 else "warning"
                    _mismatch("Quantité", po_qty, fc_qty, sev, f"Différence : {diff} ({pct:.1f}%)")
        except Exception:
            result["warnings"].append("⚠️ Quantités non comparables (donnée invalide).")

        # 3) UNITÉ
        po_u = (po.get("unite") or "").lower()
        fc_u = (facture_data.get("unite") or "").lower()
        try:
            if po_u and fc_u:
                if po_u == fc_u or self._calculate_similarity(po_u, fc_u) > 0.6:
                    result["matched_fields"].append("unite")
                else:
                    _mismatch("Unité", po_u, fc_u, "warning")
        except Exception:
            _mismatch("Unité", po_u, fc_u, "warning")

        # 4) MONTANT (prix estimé vs montant TTC)
        try:
            po_amount = float(po.get("prix_estime") or 0)
            fc_amount = float(facture_data.get("montant_ttc") or 0)

            if po_amount and fc_amount:
                diff = abs(po_amount - fc_amount)
                pct = diff / po_amount * 100
                if diff <= po_amount * 0.10:
                    result["matched_fields"].append("montant")
                else:
                    severity = "error" if pct > 15 else "warning"
                    _mismatch("Montant", po_amount, fc_amount, severity, f"Différence {pct:.1f}%")
        except Exception:
            result["warnings"].append("⚠️ Montants non comparables (format incorrect).")

        # 5) DATE DE FACTURE vs DATE DU PO (si fournie dans les deux)
        po_date = po.get("date_facture") or po.get("date") or ""
        fc_date = facture_data.get("date_facture") or ""

        if po_date and fc_date:
            if str(po_date).strip() == str(fc_date).strip():
                result["matched_fields"].append("date_facture")
            else:
                _mismatch("Date de facture", po_date, fc_date, "warning")

        # 6) CENTRE DE COÛT
        po_cc = po.get("centre_cout") or ""
        fc_cc = facture_data.get("centre_cout") or ""
        if po_cc and fc_cc:
            if po_cc == fc_cc:
                result["matched_fields"].append("centre_cout")
            else:
                _mismatch("Centre de coût", po_cc, fc_cc, "warning")

        # 7) DÉLAI SOUHAITÉ
        po_delai = po.get("delai_souhaite") or ""
        fc_delai = facture_data.get("delai_souhaite") or ""
        if po_delai and fc_delai:
            if po_delai == fc_delai:
                result["matched_fields"].append("delai_souhaite")

        # 8) DATE DE LIVRAISON
        po_dl = po.get("date_livraison_souhaitee") or po.get("date livraison souhaitée") or ""
        fc_dl = facture_data.get("date_livraison_souhaite") or ""
        if po_dl and fc_dl:
            if po_dl == fc_dl:
                result["matched_fields"].append("date_livraison")

        # 9) SPÉCIFICATIONS TECHNIQUES
        po_specs = (po.get("specifications_techniques") or "").lower()
        fc_specs = (facture_data.get("specifications_techniques") or "").lower()

        if po_specs and fc_specs:
            sim = self._calculate_similarity(po_specs, fc_specs)
            if sim > 0.80:
                result["matched_fields"].append("specifications_techniques")
            else:
                result["warnings"].append("⚠️ Les spécifications techniques semblent différentes.")

        # 10) PIÈCES / ARTICLES (si PO contient une liste d’items)
        if "items" in po and isinstance(po["items"], list):
            po_items = {str(i.get("designation", "")).lower() for i in po["items"]}
            fc_items = {str(facture_data.get("details_demande", "")).lower()}
            if po_items & fc_items:
                result["matched_fields"].append("articles")
            else:
                result["warnings"].append("⚠️ Les articles facturés ne correspondent pas clairement au PO.")

        # INTÉGRATION DU LLM
        try:
            llm = self._call_llm_compare(facture_data, po)
            if llm:
                result["llm_insights"] = llm
                print("\n--- LLM RAW OUTPUT ---")
                print(llm_insights)
                print("----------------------\n")

                # Discrepancies
                for d in llm.get("discrepancies", []):
                    _mismatch(
                        d.get("field", "inconnu"),
                        d.get("po_value"),
                        d.get("facture_value"),
                        d.get("severity", "info"),
                        d.get("reason")
                    )

                # Actions suggérées
                if llm.get("suggested_action") == "reject":
                    result["errors"].append("❌ LLM recommande de rejeter la facture.")
                    result["is_valid"] = False
                elif llm.get("suggested_action") == "review":
                    result["warnings"].append("⚠️ LLM recommande une vérification manuelle.")

                # Confiance LLM
                if llm.get("confidence") is not None:
                    result["llm_confidence"] = float(llm["confidence"])

        except Exception as e:
            result["warnings"].append(f"⚠️ Erreur LLM: {str(e)}")

        # SCORE FINAL
        TOTAL_CHECKS = 6  # ajustable
        matched = len(result["matched_fields"])
        base_score = (matched / TOTAL_CHECKS) * 100
        result["confidence_score"] = round(base_score, 1)

        # Mixer avec le score LLM si disponible
        if result.get("llm_confidence") is not None:
            result["confidence_score"] = round(
                (result["confidence_score"] + result["llm_confidence"]) / 2, 1
            )

        # Validité
        if result["confidence_score"] < 70:
            result["is_valid"] = False
            if not result["errors"]:
                result["errors"].append(
                    f"❌ Score trop faible ({result['confidence_score']}%)."
                )

        return result

    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calcule le ratio de similarité entre deux chaînes"""
        if str1 is None or str2 is None:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


# Fonction utilitaire pour valider une facture complète
def validate_facture_complete(facture_data: Dict, po_id: str, po_collection) -> Dict:
    print("\n========= FACTURE DATA DEBUG =========")
    print(facture_data)
    print("======================================\n")

    validator = FactureValidator(po_collection)
    validation_result = validator.validate_against_po(facture_data, po_id)
    
    # Log du résultat
    if validation_result["is_valid"]:
        logger.info(
            f"✅ Validation RÉUSSIE - Score: {validation_result['confidence_score']}% "
            f"({len(validation_result['matched_fields'])} champs validés)"
        )
    else:
        logger.warning(
            f"❌ Validation ÉCHOUÉE - {len(validation_result['errors'])} erreur(s), "
            f"{len(validation_result['warnings'])} avertissement(s)"
        )
    
    return validation_result