import easyocr
import re
import logging
from typing import Dict, Optional
from datetime import datetime
import numpy as np
from PIL import Image
import io
import cv2 # python module for image enhancement
import requests
import os
import json
import re as _re_for_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FactureOCREasyOCR:    
    def __init__(self, languages=['fr', 'en']):
        try:
            logger.info("🔄 Initializing EasyOCR reader...")
            self.reader = easyocr.Reader(languages, gpu=False)  # Set gpu=True if you have CUDA
            logger.info("✅ EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize EasyOCR: {e}")
            raise
    

    def parse_ocr_result(self, raw_text: str, confidence: float) -> Dict:
        # Parse OCR result into structured invoice data + OCR confidence score
        if raw_text is None:
            raw_text = ""
        
        # Ensure it's a string
        if not isinstance(raw_text, str):
            raw_text = str(raw_text) if raw_text else ""
        
        logger.info(f"🔍 Parsing extracted text into structured fields...")
        logger.info(f"📏 Text length: {len(raw_text)} characters")
        
        # Parse structured fields from raw text
        try:
            invoice_data = {
                "success": True,
                "numero_facture": self._extract_invoice_number(raw_text),
                "date_facture": self._extract_date(raw_text),
                "fournisseur_nom": self._extract_supplier(raw_text),
                "fournisseur_matricule": self._extract_matricule_fiscale(raw_text),
                "numero_po": self._extract_po_number(raw_text),
                "montant_ht": self._extract_amount(raw_text, "HT"),
                "montant_tva": self._extract_amount(raw_text, "TVA"),
                "montant_ttc": self._extract_amount(raw_text, "TTC"),
                "type_achat": self._extract_type_achat(raw_text),
                "quantite": self._extract_quantite(raw_text),
                "unite": self._extract_unite(raw_text),
                "specifications_techniques": self._extract_specifications(raw_text),
                "raw_text": raw_text,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"❌ Error parsing OCR result: {e}")
            # Return safe defaults
            invoice_data = {
                "success": True,
                "numero_facture": None,
                "date_facture": None,
                "fournisseur_nom": None,
                "fournisseur_matricule": None,
                "numero_po": None,
                "montant_ht": None,
                "montant_tva": None,
                "montant_ttc": None,

                "type_achat": "Article",
                "quantite": None,
                "unite": "pcs",
                "specifications_techniques": None,
                "raw_text": raw_text,
                "confidence": confidence
            }
        
        # Log extracted fields
        logger.info(f"📋 Extracted Fields:")
        logger.info(f"   • Numero Facture: {invoice_data['numero_facture']}")
        logger.info(f"   • Fournisseur: {invoice_data['fournisseur_nom']}")
        logger.info(f"   • Montant TTC: {invoice_data['montant_ttc']}")
        logger.info(f"   • Quantité: {invoice_data['quantite']} {invoice_data['unite']}")
        
        # Attempt to get LLM-assisted mapping (non-blocking override)
        try:
            llm_mapping = self._call_llm_map_fields(raw_text)
            if llm_mapping:
                # Allowed keys to merge
                merge_keys = [
                    "numero_facture", "date_facture", "fournisseur_nom", "fournisseur_matricule",
                    "numero_po", "montant_ht", "montant_tva", "montant_ttc",
                    "type_achat", "quantite", "unite", "specifications_techniques"
                ]
                for k in merge_keys:
                    if k in llm_mapping and llm_mapping[k] is not None:
                        try:
                            # Cast numeric fields where appropriate
                            if k in ("montant_ht", "montant_tva", "montant_ttc"):
                                invoice_data[k] = float(llm_mapping[k])
                            elif k == "quantite":
                                invoice_data[k] = int(llm_mapping[k]) if llm_mapping[k] != "" else invoice_data.get(k)
                            else:
                                invoice_data[k] = llm_mapping[k]
                        except Exception:
                            # If casting fails, keep original parsed value
                            logger.debug(f"⚠️ Failed to cast LLM value for {k}: {llm_mapping[k]}")
        except Exception as e:
            logger.debug(f"⚠️ LLM merge skipped due to error: {e}")

        return invoice_data
    
    def extract_from_bytes(self, image_bytes: bytes) -> Dict:
        # Extract text from image bytes
        try:
            logger.info("🔍 Starting OCR extraction from bytes...")
            
            # Convert bytes to numpy array for EasyOCR
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Perform OCR
            logger.info("📖 Running EasyOCR text detection...")
            results = self.reader.readtext(img_array)
            
            # Extract all text with confidence scores
            extracted_text = []
            total_confidence = 0
            
            for (bbox, text, confidence) in results:
                extracted_text.append(text)
                total_confidence += confidence
            
            # Join all text
            raw_text = "\n".join(extracted_text)
            avg_confidence = total_confidence / len(results) if results else 0.0
            
            logger.info(f"✅ OCR completed - Extracted {len(results)} text blocks")
            logger.info(f"📊 Average confidence: {avg_confidence*100:.1f}%")
            logger.info(f"📄 Extracted text length: {len(raw_text)} characters")
            
            # Parse the extracted text into structured data
            invoice_data = self.parse_ocr_result(raw_text, avg_confidence)
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"❌ OCR extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": "",
                "confidence": 0.0
            }
    
    def extract_from_file(self, file_path: str) -> Dict:
        """
        Extract text from image file using EasyOCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted invoice data dictionary
        """
        try:
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            return self.extract_from_bytes(image_bytes)
        except Exception as e:
            logger.error(f"❌ Failed to read file: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": "",
                "confidence": 0.0
            }
    
    def preprocess_image(self, image_bytes: bytes) -> bytes:
        # Preprocess image for better OCR accuracy (optional enhancement)
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to bytes
            is_success, buffer = cv2.imencode(".png", thresh)
            if is_success:
                return buffer.tobytes()
            else:
                return image_bytes
                
        except Exception as e:
            logger.warning(f"⚠️ Preprocessing failed, using original image: {e}")
            return image_bytes
    
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number"""
        # Safety check
        if text is None or not isinstance(text, str) or not text.strip():
            return None
            
        try:
            patterns = [
                r'(?:FACTURE|INVOICE|N°|NO|#|NUM)\s*[:.]?\s*([A-Z0-9-]+)',
                r'(?:F|INV)[-/]?(\d{4,})',
                r'N°\s*([A-Z0-9-]{3,})',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        except Exception:
            pass
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract invoice date"""
        if not text:
            return None
            
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:Jan|Fév|Fev|Mar|Avr|Mai|Juin|Juil|Août|Aout|Sep|Oct|Nov|Déc|Dec)[a-z]*\s+\d{4})',
            r'(?:Date|DATE)\s*[:.]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_supplier(self, text: str) -> Optional[str]:
        """
        Strategy:
        - Scan the first N lines (header zone).
        - Skip lines that look like titles, contact info, addresses, or numeric-only lines.
        - Score remaining lines using company keywords, uppercase signals, word counts.
        - Prefer lines that are near a detected fiscal/matricule/VAT line (if available).
        - Return the highest scoring candidate or None if none pass thresholds.
        """

        if not text or not isinstance(text, str):
            return None

        try:
            lines = [ln.strip() for ln in text.splitlines()]
            if not lines:
                return None

            # Header zone — tune as needed
            HEADER_LINES = 20
            header = lines[:HEADER_LINES]

            # Precompiled regexes
            email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
            
            only_digits_re = re.compile(r'^[\d\W_]+$')
            invoice_title_re = re.compile(r'\b(Facture|Invoice|Reçu|Receipt|Bill)\b', re.I)
            address_tokens = re.compile(r'\b(Rue|Av\.|Avenue|Boulevard|Boulv|BP|P\.O\. Box|Po Box|Address|Adresse)\b', re.I)
            company_keywords = re.compile(r'\b(SARL|S\.A\.R\.L|S A R L|SAS|SASU|SA|Ltd|LLC|GmbH|Inc|Entreprise|Soci[eé]t[eé]|Company|Corporation)\b', re.I)

            

            candidates = []
            for idx, ln in enumerate(header):
                if not ln:
                    continue
                # normalize whitespace
                norm = ' '.join(ln.split())

                # Skip obvious non-supplier lines
                if len(norm) < 3 or len(norm) > 120:
                    continue
                if only_digits_re.match(norm):
                    continue
                if invoice_title_re.search(norm):
                    continue

                if address_tokens.search(norm):
                    # likely an address line, skip (supplier name might be above)
                    continue
                # skip lines that are mainly currency amounts or contain currency symbols
                if re.search(r'[\€\$\£]|(?<!\d)\d{1,3}(?:[.,]\d{3})*[.,]\d{2}', norm):
                    continue

                # Heuristics scoring
                score = 0
                words = norm.split()
                alpha_words = [w for w in words if re.search(r'[A-Za-zÀ-ÖØ-öø-ÿ]', w)]
                if len(alpha_words) >= 1:
                    score += min(len(alpha_words), 5)  # more alphabetic words is slightly better

                # company keyword bonus
                if company_keywords.search(norm):
                    score += 10

                # uppercase words bonus (common in headers)
                uppercase_words = sum(1 for w in words if w.isupper() and len(w) > 1)
                score += uppercase_words * 2

                # penalize if it contains words like 'client' or 'destinataire'
                if re.search(r'\b(Client|Destinataire|Bill To|Billed To)\b', norm, re.I):
                    score -= 5


                candidates.append((score, idx, norm))

            if not candidates:
                return None

            # pick highest scoring candidate
            candidates.sort(reverse=True, key=lambda x: (x[0], -x[1]))
            best_score, best_idx, best_line = candidates[0]

            # threshold to avoid returning spurious results
            if best_score < 2:
                # LLM fallback
                self._call_llm_map_fields(text)

            # final cleanup: remove trailing words like "SIRET:" or phone leftovers
            cleaned = re.sub(r'\b(SIRET|SIREN|TVA|RC|Matricule|N[o°]+)\b[:\s]*\S*', '', best_line, flags=re.I)
            cleaned = re.sub(r'[^\w\s\-\.,&()\/]', '', cleaned).strip()
            # collapse whitespace
            cleaned = ' '.join(cleaned.split())
            return cleaned if cleaned else None

        except Exception:
            return None


    
    def _extract_matricule_fiscale(self, text: str) -> Optional[str]:
        """Extract Tunisian fiscal ID"""
        if not text:
            return None
            
        patterns = [
            r'(?:MF|TVA|SIRET|SIREN|RC|Matricule|N° TVA|Numéro TVA|Matricule fiscal)\s*[:.]?\s*(\d{7}[A-Z]{3}\d{3})',
            r'(\d{7}[A-Z]{3}\d{3})',  # Direct pattern for Tunisian MF
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_po_number(self, text: str) -> Optional[str]:
        """Extract Purchase Order number"""
        if not text:
            return None
            
        patterns = [
            r'(?:PO|Purchase Order|Bon de commande|BC)\s*[:.]?\s*([A-Z0-9-]+)',
            r'PO[-\s]?([A-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_unite(self, text: str) -> str:
        """Extract unit"""
        # Extra safety: handle None, empty string, or any non-string type
        if text is None or not isinstance(text, str):
            return "pcs"  # Default
            
        units = ['pcs', 'pièce', 'pièces', 'piéces', 'kg', 'litre', 'mètre', 'metre', 'heure', 'jour', 'unit', 'unité']
        
        try:
            for unit in units:
                if unit in text:
                    if unit in ['pcs', 'pièce', 'pièces', 'piéces', 'unit', 'unité']:
                        return "pcs"
                    return unit
        except (AttributeError, TypeError):
            pass
        
        return "pcs"  # Default
    
    def _extract_amount(self, text: str, amount_type: str) -> Optional[float]:
        """Extract amount (HT, TVA, or TTC)"""
        if not text:
            return None
            
        patterns = {
            "HT": [
                r'(?:Montant HT|Sous[-\s]?total|HT|Hors Taxes)\s*[:.]?\s*([\d\s,\.]+)',
                r'HT\s*[:.]?\s*([\d\s,\.]+)',
            ],
            "TVA": [
                r'(?:TVA|Tax|Taxes)\s*[:.]?\s*([\d\s,\.]+)',
                r'TVA\s*\(?\d+%?\)?\s*[:.]?\s*([\d\s,\.]+)',
            ],
            "TTC": [
                r'(?:Total TTC|Total|TOTAL|Montant Total)\s*[:.]?\s*([\d\s,\.]+)',
                r'TTC\s*[:.]?\s*([\d\s,\.]+)',
            ]
        }
        
        pattern_list = patterns.get(amount_type.upper(), [])
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(' ', '').replace(',', '.')
                # Remove any non-digit/dot characters
                amount_str = re.sub(r'[^\d.]', '', amount_str)
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def _extract_type_achat(self, text: str) -> str:
        """Extract purchase type"""
        # Extra safety: handle None, empty string, or any non-string type
        if text is None or not isinstance(text, str) or not text.strip():
            return "Article"  # Default
            
        types = {
            'Article': ['article', 'produit', 'matériel', 'matériau', 'équipement', 'fourniture'],
            'Service': ['service', 'prestation', 'consultation', 'maintenance'],
            'CAPEX': ['capex', 'investissement', 'immobilisation', 'capital'],
            'Contrat': ['contrat', 'abonnement', 'subscription'],
        }
        
        try:
            for type_name, keywords in types.items():
                if any(keyword in text for keyword in keywords):
                    return type_name
        except (AttributeError, TypeError):
            pass
        
        return "Article"  # Default
    
    def _extract_quantite(self, text: str) -> Optional[int]:
        """Extract quantity"""
        if not text:
            return None
            
        patterns = [
            r'(?:Quantité|Qté|QTE|Quantity|Qty)\s*[:.]?\s*(\d+)',
            r'(\d+)\s+(?:pcs|pièces|piéces|unités|unites|units)',
            r'Qté\s*[:.]?\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_unite(self, text: str) -> str:

        if text is None or not isinstance(text, str):
            return "pcs"  # Default
            
        units = ['pcs', 'pièce', 'pièces', 'piéces', 'kg', 'litre', 'mètre', 'metre', 'heure', 'jour', 'unit', 'unité']
        
        try:

            for unit in units:
                if unit in text:
                    if unit in ['pcs', 'pièce', 'pièces', 'piéces', 'unit', 'unité']:
                        return "pcs"
                    return unit
        except (AttributeError, TypeError):
            pass
        
        return "pcs"  # Default
    
    def _extract_specifications(self, text: str) -> Optional[str]:
        """Extract technical specifications (simplified)"""
        if not text:
            return None
            
        # Look for detailed descriptions
        patterns = [
            r'(?:Description|Spécifications|Specifications|Details|Détails)\s*[:.]?\s*(.{20,200})',
            r'(?:Caractéristiques|Features|Reference|Référence)\s*[:.]?\s*(.{20,200})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                spec_text = match.group(1).strip()
                # Clean up newlines and extra spaces
                spec_text = re.sub(r'\s+', ' ', spec_text)
                return spec_text[:200]  # Limit to 200 chars
        return None
    
    def _call_llm_map_fields(self, raw_text: str) -> Dict:
        """
            map raw OCR text into the predefined invoice fields.
            numero_facture, date_facture, fournisseur_nom, fournisseur_matricule,
            numero_po, montant_ht, montant_tva, montant_ttc,type_achat,
            quantite, unite, specifications_techniques
        """
        RAPIDAPI_URL = os.getenv("RAPIDAPI_URL")
        RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
        RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

        if not RAPIDAPI_URL or not RAPIDAPI_KEY:
            logger.warning("⚠️ RapidAPI URL/KEY not set; skipping LLM mapping.")
            return {}

        # Build instruction for the LLM. Keep it strict: output **only** a JSON object.
        system_prompt = (
            "You are a JSON extractor. Given raw OCR text of an invoice in French or English, "
            "strictly return a JSON object (no explanatory text) with the following keys: "
            "numero_facture, date_facture, fournisseur_nom, fournisseur_matricule, numero_po, "
            "montant_ht, montant_tva, montant_ttc,type_achat, quantite, unite, "
            "specifications_techniques. Use null for missing values. "
            "Dates should be ISO (YYYY-MM-DD) if possible. Numbers should be plain numerics (no currency symbols)."
        )

        user_prompt = f"Extract invoice fields from the OCRed text below. Return ONLY a single JSON object.\n\n---OCR TEXT BEGIN---\n{raw_text}\n---OCR TEXT END---"

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "web_access": False
        }

        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST if RAPIDAPI_HOST else "",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=60)
        except Exception as e:
            logger.warning(f"⚠️ LLM request failed: {e}")
            return {}

        if not resp.ok:
            logger.warning(f"⚠️ LLM responded with HTTP {resp.status_code}: {resp.text[:500]}")
            return {}

        # Try to parse likely response shapes robustly:
        try:
            data = resp.json()
        except ValueError:
            # Response not JSON — try to parse body text
            raw = resp.text
            # attempt to extract a JSON substring
            m = _re_for_json.search(r'(\{[\s\S]*\})', raw)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    return {}
            return {}

        # If JSON, try common formats:
        # 1) OpenAI-like: {"choices":[{"message":{"content":"{...}"}}]}
        try:
            if isinstance(data, dict):
                # OpenAI-like
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
                        # extract JSON substring if there is extra
                        m = _re_for_json.search(r'(\{[\s\S]*\})', content)
                        if m:
                            try:
                                return json.loads(m.group(1))
                            except Exception:
                                pass
                        # otherwise try parse directly
                        try:
                            return json.loads(content)
                        except Exception:
                            pass

                # 2) Some endpoints provide 'output' or 'response' fields
                for k in ("output", "response", "result", "data"):
                    if k in data:
                        val = data[k]
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
                        elif isinstance(val, dict):
                            return val

                # 3) If the top-level JSON **is** the object we need
                # Validate it has at least one of our target keys:
                expected_keys = {
                    "numero_facture", "date_facture", "fournisseur_nom",
                    "fournisseur_matricule", "numero_po", "montant_ht",
                    "montant_tva", "montant_ttc","type_achat",
                    "quantite", "unite", "specifications_techniques"
                }
                if expected_keys & set(data.keys()):
                    return data

        except Exception as e:
            logger.debug(f"🔎 Error while trying to interpret LLM JSON: {e}")

        # Fallback: try to find a JSON blob anywhere in the entire data string
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

        # Nothing parseable
        logger.warning("⚠️ LLM returned no parseable JSON mapping.")
        return {}

# _______________________________________________________________
# Example usage function
# _______________________________________________________________
def process_facture_from_bytes(image_bytes: bytes) -> Dict:
    """
    Complete workflow: Extract invoice data from image bytes
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Extracted invoice data
    """
    ocr = FactureOCREasyOCR(languages=['fr', 'en'])
    result = ocr.extract_from_bytes(image_bytes)
    
    if result.get("success"):
        logger.info(f"✅ Invoice extraction completed")
        logger.info(f"   Numero: {result.get('numero_facture')}")
        logger.info(f"   Fournisseur: {result.get('fournisseur_nom')}")
        logger.info(f"   Montant TTC: {result.get('montant_ttc')} DT")
    else:
        logger.error(f"❌ Extraction failed: {result.get('error')}")
    
    return result


def process_facture_from_file(file_path: str) -> Dict:

    # Complete workflow: Extract invoice data from file
    ocr = FactureOCREasyOCR(languages=['fr', 'en'])
    result = ocr.extract_from_file(file_path)
    
    if result.get("success"):
        logger.info(f"✅ Invoice extraction completed")
        logger.info(f"   Numero: {result.get('numero_facture')}")
        logger.info(f"   Fournisseur: {result.get('fournisseur_nom')}")
        logger.info(f"   Montant TTC: {result.get('montant_ttc')} DT")
    else:
        logger.error(f"❌ Extraction failed: {result.get('error')}")
    
    return result