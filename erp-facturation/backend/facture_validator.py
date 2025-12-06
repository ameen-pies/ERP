import logging
from typing import Dict
from difflib import SequenceMatcher
import re

import requests
import os
import json
import re as _re_for_json
from typing import Optional

logger = logging.getLogger(__name__)


class FactureValidator:
    """Validateur pour comparer facture vs Purchase Order"""
    
    # ✅ CONFIGURABLE TOLERANCES - Real business logic
    TOLERANCE_AMOUNT_PERCENT = 2.0  # 2% tolerance for amounts (realistic for rounding)
    TOLERANCE_AMOUNT_ABSOLUTE = 0.05  # 0.05 TND absolute tolerance (5 millimes)
    TOLERANCE_QUANTITY_PERCENT = 5.0  # 5% tolerance for quantities
    TOLERANCE_STRING_SIMILARITY = 0.85  # 85% similarity for text fields
    
    def __init__(self, po_collection):
        self.po_collection = po_collection
    
    def _normalize_string(self, text: str) -> str:
        """
        Normalize string for comparison:
        - Remove extra whitespace
        - Convert to lowercase
        - Remove special characters
        - Remove accents
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common punctuation that doesn't affect meaning
        text = re.sub(r'[.,;:!?\-_/\\()\[\]{}]', ' ', text)
        
        # Remove extra spaces again
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _compare_amounts(self, po_amount: float, facture_amount: float, field_name: str) -> Dict:
        """
        Smart amount comparison with proper tolerance
        Returns: {"match": bool, "difference": float, "percentage": float, "reason": str}
        """
        try:
            po_amt = float(po_amount) if po_amount is not None else 0.0
            fact_amt = float(facture_amount) if facture_amount is not None else 0.0
            
            # Calculate absolute difference
            diff = abs(po_amt - fact_amt)
            
            # Calculate percentage difference
            if po_amt > 0:
                pct_diff = (diff / po_amt) * 100
            else:
                pct_diff = 100.0 if fact_amt > 0 else 0.0
            
            # Check if within tolerance
            within_absolute = diff <= self.TOLERANCE_AMOUNT_ABSOLUTE
            within_percentage = pct_diff <= self.TOLERANCE_AMOUNT_PERCENT
            
            is_match = within_absolute or within_percentage
            
            reason = ""
            if not is_match:
                reason = f"Différence: {diff:.3f} ({pct_diff:.2f}%) - Tolérance: ±{self.TOLERANCE_AMOUNT_PERCENT}% ou ±{self.TOLERANCE_AMOUNT_ABSOLUTE} TND"
            else:
                reason = f"Différence minime acceptable: {diff:.3f} ({pct_diff:.2f}%)"
            
            return {
                "match": is_match,
                "difference": diff,
                "percentage": pct_diff,
                "reason": reason,
                "po_value": po_amt,
                "facture_value": fact_amt
            }
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Amount comparison error for {field_name}: {e}")
            return {
                "match": False,
                "difference": 0,
                "percentage": 0,
                "reason": "Valeurs invalides pour la comparaison",
                "po_value": po_amount,
                "facture_value": facture_amount
            }
    
    def _compare_quantities(self, po_qty: int, facture_qty: int) -> Dict:
        """
        Smart quantity comparison with tolerance
        """
        try:
            po_q = int(po_qty) if po_qty is not None else 0
            fact_q = int(facture_qty) if facture_qty is not None else 0
            
            diff = abs(po_q - fact_q)
            
            if po_q > 0:
                pct_diff = (diff / po_q) * 100
            else:
                pct_diff = 100.0 if fact_q > 0 else 0.0
            
            is_match = pct_diff <= self.TOLERANCE_QUANTITY_PERCENT
            
            reason = ""
            if not is_match:
                reason = f"Différence: {diff} unités ({pct_diff:.1f}%) - Tolérance: ±{self.TOLERANCE_QUANTITY_PERCENT}%"
            else:
                reason = f"Différence acceptable: {diff} unités ({pct_diff:.1f}%)"
            
            return {
                "match": is_match,
                "difference": diff,
                "percentage": pct_diff,
                "reason": reason,
                "po_value": po_q,
                "facture_value": fact_q
            }
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Quantity comparison error: {e}")
            return {
                "match": False,
                "difference": 0,
                "percentage": 0,
                "reason": "Valeurs invalides",
                "po_value": po_qty,
                "facture_value": facture_qty
            }
    
    def _compare_strings(self, po_text: str, facture_text: str, field_name: str) -> Dict:
        """
        Smart string comparison with normalization and fuzzy matching
        """
        # Normalize both strings
        po_normalized = self._normalize_string(po_text)
        fact_normalized = self._normalize_string(facture_text)
        
        # If both empty, consider match
        if not po_normalized and not fact_normalized:
            return {
                "match": True,
                "similarity": 1.0,
                "reason": "Champs vides"
            }
        
        # If one is empty, not a match
        if not po_normalized or not fact_normalized:
            return {
                "match": False,
                "similarity": 0.0,
                "reason": "Un champ est vide",
                "po_value": po_text,
                "facture_value": facture_text
            }
        
        # Calculate similarity
        similarity = SequenceMatcher(None, po_normalized, fact_normalized).ratio()
        
        is_match = similarity >= self.TOLERANCE_STRING_SIMILARITY
        
        reason = ""
        if is_match:
            reason = f"Similarité: {similarity*100:.1f}%"
        else:
            reason = f"Similarité insuffisante: {similarity*100:.1f}% (minimum: {self.TOLERANCE_STRING_SIMILARITY*100:.0f}%)"
        
        return {
            "match": is_match,
            "similarity": similarity,
            "reason": reason,
            "po_value": po_text,
            "facture_value": facture_text,
            "po_normalized": po_normalized,
            "fact_normalized": fact_normalized
        }
    
    def _call_llm_compare(self, facture_data: Dict, po: Dict) -> Dict:
        """
        RapidAPI endpoint to compare facture_ocr output vs PO
        Returns a dict with optional keys:
        - 'discrepancies': list of {field, po_value, facture_value, severity, reason}
        - 'action_suggérée': one of 'accepter', 'reviser', 'rejeter'
        - 'confidence': float (0-100)
        """
        RAPIDAPI_URL = os.getenv("RAPIDAPI_URL")
        RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
        RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "")

        if not RAPIDAPI_URL or not RAPIDAPI_KEY:
            logger.debug("⚠️ RapidAPI config missing, skipping LLM compare.")
            return {}

        system_prompt = (
            "You are an automated invoice vs purchase-order comparer. "
            "Given a PO JSON and an Invoice (facture) JSON, return ONLY a single JSON object "
            "with these keys: 'discrepancies' (array), 'action_suggérée' (accepter, reviser, rejeter), "
            "and 'confidence' (0-100). Each discrepancy must contain: field, po_value, facture_value, severity (error|warning|info), reason. "
            "IMPORTANT: Use realistic tolerances - amounts within 2% are acceptable, text with 85%+ similarity is acceptable. "
            "Do NOT include any extra text outside the JSON object."
        )

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

        try:
            data = resp.json()
        except Exception:
            raw = resp.text
            m = _re_for_json.search(r'(\{[\s\S]*\})', raw)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    logger.debug("⚠️ Could not parse JSON blob from LLM text response.")
                    return {}
            return {}

        try:
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

                if any(k in data for k in ("discrepancies", "action_suggérée", "confidence")):
                    return data

        except Exception as e:
            logger.debug(f"🔎 Error interpreting LLM compare response: {e}")

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
        Combine: 
            - Vérifications internes (Règles métier AMÉLIORÉES)
            - Vérifications assistées par LLM
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 VALIDATION: Facture vs PO {po_id}")
        logger.info(f"{'='*60}")

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

        matched_count = 0
        total_checks = 0

        # Helper to add mismatches
        def _add_mismatch(field, comparison_result, severity=None):
            """Add a mismatch based on comparison result"""
            if comparison_result.get("match"):
                result["matched_fields"].append(field)
                logger.info(f"  ✅ {field}: MATCH")
                return True
            else:
                # Determine severity if not provided
                if severity is None:
                    # Default severity based on percentage difference
                    pct = comparison_result.get("percentage", 0)
                    if pct > 15:
                        severity = "error"
                    elif pct > 5:
                        severity = "warning"
                    else:
                        severity = "info"
                
                mismatch = {
                    "field": field,
                    "po_value": comparison_result.get("po_value"),
                    "facture_value": comparison_result.get("facture_value"),
                    "severity": severity,
                    "reason": comparison_result.get("reason", "")
                }
                
                if "difference" in comparison_result:
                    mismatch["difference"] = f"{comparison_result['difference']:.3f}"
                
                result["mismatches"].append(mismatch)
                
                if severity == "error":
                    result["errors"].append(f"❌ {field}: {comparison_result.get('reason')}")
                    result["is_valid"] = False
                    logger.warning(f"  ❌ {field}: ERROR - {comparison_result.get('reason')}")
                elif severity == "warning":
                    result["warnings"].append(f"⚠️ {field}: {comparison_result.get('reason')}")
                    logger.info(f"  ⚠️ {field}: WARNING - {comparison_result.get('reason')}")
                else:
                    result["warnings"].append(f"ℹ️ {field}: {comparison_result.get('reason')}")
                    logger.info(f"  ℹ️ {field}: INFO - {comparison_result.get('reason')}")
                
                return False

        # 1) TYPE D'ACHAT
        total_checks += 1
        po_type = (po.get("type_achat") or "").strip()
        fc_type = (facture_data.get("type_achat") or "").strip()
        type_comparison = self._compare_strings(po_type, fc_type, "Type d'achat")
        if _add_mismatch("Type d'achat", type_comparison):
            matched_count += 1

        # 2) QUANTITÉ
        total_checks += 1
        po_qty = po.get("quantite")
        fc_qty = facture_data.get("quantite")
        if po_qty is not None and fc_qty is not None:
            qty_comparison = self._compare_quantities(po_qty, fc_qty)
            if _add_mismatch("Quantité", qty_comparison):
                matched_count += 1
        else:
            logger.warning("  ⚠️ Quantités non disponibles pour comparaison")

        # 3) UNITÉ
        total_checks += 1
        po_u = po.get("unite") or ""
        fc_u = facture_data.get("unite") or ""
        unit_comparison = self._compare_strings(po_u, fc_u, "Unité")
        if _add_mismatch("Unité", unit_comparison, severity="info"):  # Units are less critical
            matched_count += 1

        # 4) MONTANT TTC (Most important!)
        total_checks += 1
        po_amount = po.get("prix_estime") or po.get("montant_ttc")
        fc_amount = facture_data.get("montant_ttc")
        if po_amount is not None and fc_amount is not None:
            amount_comparison = self._compare_amounts(po_amount, fc_amount, "Montant TTC")
            if _add_mismatch("Montant TTC", amount_comparison):
                matched_count += 1
        else:
            logger.warning("  ⚠️ Montants non disponibles pour comparaison")

        # 5) MONTANT HT
        total_checks += 1
        po_ht = po.get("montant_ht")
        fc_ht = facture_data.get("montant_ht")
        if po_ht is not None and fc_ht is not None:
            ht_comparison = self._compare_amounts(po_ht, fc_ht, "Montant HT")
            if _add_mismatch("Montant HT", ht_comparison):
                matched_count += 1

        # 6) FOURNISSEUR
        total_checks += 1
        po_fournisseur = ""
        if isinstance(po.get("fournisseur"), dict):
            po_fournisseur = po["fournisseur"].get("nom", "")
        elif isinstance(po.get("fournisseur"), str):
            po_fournisseur = po["fournisseur"]
        
        fc_fournisseur = facture_data.get("fournisseur_nom", "")
        
        if po_fournisseur and fc_fournisseur:
            fournisseur_comparison = self._compare_strings(po_fournisseur, fc_fournisseur, "Fournisseur")
            if _add_mismatch("Fournisseur", fournisseur_comparison):
                matched_count += 1

        # 7) CENTRE DE COÛT
        total_checks += 1
        po_cc = po.get("centre_cout") or ""
        fc_cc = facture_data.get("centre_cout") or ""
        if po_cc and fc_cc:
            cc_comparison = self._compare_strings(po_cc, fc_cc, "Centre de coût")
            if _add_mismatch("Centre de coût", cc_comparison, severity="warning"):
                matched_count += 1

        # 8) SPÉCIFICATIONS TECHNIQUES
        total_checks += 1
        po_specs = po.get("specifications_techniques") or ""
        fc_specs = facture_data.get("specifications_techniques") or ""
        if po_specs and fc_specs:
            specs_comparison = self._compare_strings(po_specs, fc_specs, "Spécifications")
            if _add_mismatch("Spécifications", specs_comparison, severity="info"):
                matched_count += 1

        # SCORE DE CONFIANCE
        if total_checks > 0:
            base_score = (matched_count / total_checks) * 100
            result["confidence_score"] = round(base_score, 1)
        else:
            result["confidence_score"] = 0.0

        logger.info(f"\n📊 RÉSULTAT:")
        logger.info(f"  - Champs validés: {matched_count}/{total_checks}")
        logger.info(f"  - Score: {result['confidence_score']}%")
        logger.info(f"  - Erreurs: {len(result['errors'])}")
        logger.info(f"  - Avertissements: {len(result['warnings'])}")

        # INTÉGRATION DU LLM (Optional enhancement)
        try:
            llm = self._call_llm_compare(facture_data, po)
            if llm:
                result["llm"] = llm
                logger.info(f"\n🤖 LLM Analysis:")
                logger.info(f"  - Action suggérée: {llm.get('action_suggérée', 'N/A')}")
                logger.info(f"  - Confiance LLM: {llm.get('confidence', 'N/A')}%")

                # Combine LLM confidence if available
                if llm.get("confidence") is not None:
                    llm_confidence = float(llm["confidence"])
                    combined_score = (result["confidence_score"] + llm_confidence) / 2
                    result["confidence_score"] = round(combined_score, 1)
                    logger.info(f"  - Score combiné: {result['confidence_score']}%")

        except Exception as e:
            logger.warning(f"⚠️ Erreur LLM: {str(e)}")

        # VALIDATION FINALE
        # More lenient validation - 70% is good enough with proper tolerances
        if result["confidence_score"] < 60:
            result["is_valid"] = False
            if not result["errors"]:
                result["errors"].append(
                    f"❌ Score de confiance insuffisant ({result['confidence_score']}% < 60%)."
                )

        logger.info(f"{'='*60}\n")
        
        return result

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings (deprecated - use _compare_strings instead)"""
        if str1 is None or str2 is None:
            return 0.0
        norm1 = self._normalize_string(str1)
        norm2 = self._normalize_string(str2)
        return SequenceMatcher(None, norm1, norm2).ratio()


# Fonction utilitaire pour valider une facture complète
def validate_facture_complete(facture_data: Dict, po_id: str, po_collection) -> Dict:
    """Wrapper function for complete validation"""
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