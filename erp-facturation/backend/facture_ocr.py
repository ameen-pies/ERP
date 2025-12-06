import easyocr
import re
import logging
from typing import Dict, Optional
from datetime import datetime
import numpy as np
from PIL import Image
import io
import cv2
import requests
import os
import json
import re as _re_for_json
import fitz  # PyMuPDF for PDF handling

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FactureOCREasyOCR:    
    def __init__(self, languages=['fr', 'en']):
        try:
            logger.info("📄 Initializing EasyOCR reader...")
            self.reader = easyocr.Reader(languages, gpu=False)
            logger.info("✅ EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize EasyOCR: {e}")
            raise
    
    def _is_pdf(self, file_bytes: bytes) -> bool:
        """Check if file is a PDF by checking magic bytes"""
        return file_bytes[:4] == b'%PDF'
    
    def _pdf_to_images(self, pdf_bytes: bytes) -> list:
        """Convert PDF pages to PIL Images"""
        try:
            logger.info("📄 Converting PDF to images...")
            
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            images = []
            
            # Convert each page to image
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to pixmap (image) at 300 DPI for better OCR
                mat = fitz.Matrix(300/72, 300/72)  # 300 DPI
                pix = page.get_pixmap(matrix=mat)
                
                # Convert pixmap to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                images.append(img)
                logger.info(f"✅ Converted PDF page {page_num + 1}/{len(pdf_document)}")
            
            pdf_document.close()
            logger.info(f"✅ PDF converted to {len(images)} image(s)")
            return images
            
        except Exception as e:
            logger.error(f"❌ PDF conversion failed: {e}")
            raise Exception(f"Failed to convert PDF to images: {str(e)}")
    
    def extract_from_bytes(self, image_bytes: bytes) -> Dict:
        """Extract text from image or PDF bytes"""
        try:
            logger.info("🔍 Starting OCR extraction from bytes...")
            
            # Check if it's a PDF
            if self._is_pdf(image_bytes):
                logger.info("📄 PDF file detected, converting to images...")
                images = self._pdf_to_images(image_bytes)
                
                # Process all pages and combine results
                all_text = []
                all_confidences = []
                
                for idx, img in enumerate(images):
                    logger.info(f"🔖 Processing page {idx + 1}/{len(images)}...")
                    
                    # Convert PIL Image to numpy array
                    img_array = np.array(img)
                    
                    # Perform OCR on this page
                    results = self.reader.readtext(img_array)
                    
                    for (bbox, text, confidence) in results:
                        all_text.append(text)
                        all_confidences.append(confidence)
                
                # Combine all text from all pages
                raw_text = "\n".join(all_text)
                avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
                
                logger.info(f"✅ PDF OCR completed - {len(images)} pages, {len(all_text)} text blocks")
                
            else:
                # It's an image file
                logger.info("🖼️ Image file detected...")
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
                all_text = []
                all_confidences = []
                
                for (bbox, text, confidence) in results:
                    all_text.append(text)
                    all_confidences.append(confidence)
                
                raw_text = "\n".join(all_text)
                avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
                
                logger.info(f"✅ Image OCR completed - {len(results)} text blocks")
            
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
                "devise": self._extract_devise(raw_text),
                "type_achat": self._extract_type_achat(raw_text),
                "quantite": self._extract_quantite(raw_text),
                "unite": self._extract_unite(raw_text),
                "specifications_techniques": self._extract_specifications(raw_text),
                "raw_text": raw_text,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"❌ Error parsing OCR result: {e}")
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
                "devise": "TND",
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
                merge_keys = [
                    "numero_facture", "date_facture", "fournisseur_nom", "fournisseur_matricule",
                    "numero_po", "montant_ht", "montant_tva", "montant_ttc",
                    "type_achat", "quantite", "unite", "specifications_techniques"
                ]
                for k in merge_keys:
                    if k in llm_mapping and llm_mapping[k] is not None:
                        try:
                            if k in ("montant_ht", "montant_tva", "montant_ttc"):
                                invoice_data[k] = float(llm_mapping[k])
                            elif k == "quantite":
                                invoice_data[k] = int(llm_mapping[k]) if llm_mapping[k] != "" else invoice_data.get(k)
                            else:
                                invoice_data[k] = llm_mapping[k]
                        except Exception:
                            logger.debug(f"⚠️ Failed to cast LLM value for {k}: {llm_mapping[k]}")
        except Exception as e:
            logger.debug(f"⚠️ LLM merge skipped due to error: {e}")

        return invoice_data
    
    def extract_from_file(self, file_path: str) -> Dict:
        """Extract text from image or PDF file"""
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            return self.extract_from_bytes(file_bytes)
        except Exception as e:
            logger.error(f"❌ Failed to read file: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": "",
                "confidence": 0.0
            }
    
    def _extract_devise(self, text: str) -> str:
        """Extract currency"""
        if not text:
            return "TND"
        
        # Look for currency codes or symbols
        currencies = {
            'TND': ['TND', 'DT', 'Dinar'],
            'EUR': ['EUR', '€', 'Euro'],
            'USD': ['USD', '$', 'Dollar'],
        }
        
        for code, patterns in currencies.items():
            for pattern in patterns:
                if pattern in text:
                    return code
        
        return "TND"  # Default
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number"""
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
        """Extract supplier name"""
        if not text or not isinstance(text, str):
            return None

        try:
            lines = [ln.strip() for ln in text.splitlines()]
            if not lines:
                return None

            HEADER_LINES = 20
            header = lines[:HEADER_LINES]

            email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
            only_digits_re = re.compile(r'^[\d\W_]+$')
            invoice_title_re = re.compile(r'\b(Facture|Invoice|Reçu|Receipt|Bill)\b', re.I)
            address_tokens = re.compile(r'\b(Rue|Av\.|Avenue|Boulevard|Boulv|BP|P\.O\. Box|Po Box|Address|Adresse)\b', re.I)
            company_keywords = re.compile(r'\b(SARL|S\.A\.R\.L|S A R L|SAS|SASU|SA|Ltd|LLC|GmbH|Inc|Entreprise|Soci[eé]t[eé]|Company|Corporation)\b', re.I)

            candidates = []
            for idx, ln in enumerate(header):
                if not ln:
                    continue
                norm = ' '.join(ln.split())

                if len(norm) < 3 or len(norm) > 120:
                    continue
                if only_digits_re.match(norm):
                    continue
                if invoice_title_re.search(norm):
                    continue
                if address_tokens.search(norm):
                    continue
                if re.search(r'[€\$\£]|(?<!\d)\d{1,3}(?:[.,]\d{3})*[.,]\d{2}', norm):
                    continue

                score = 0
                words = norm.split()
                alpha_words = [w for w in words if re.search(r'[A-Za-zÀ-ÖØ-öø-ÿ]', w)]
                if len(alpha_words) >= 1:
                    score += min(len(alpha_words), 5)

                if company_keywords.search(norm):
                    score += 10

                uppercase_words = sum(1 for w in words if w.isupper() and len(w) > 1)
                score += uppercase_words * 2

                if re.search(r'\b(Client|Destinataire|Bill To|Billed To)\b', norm, re.I):
                    score -= 5

                candidates.append((score, idx, norm))

            if not candidates:
                return None

            candidates.sort(reverse=True, key=lambda x: (x[0], -x[1]))
            best_score, best_idx, best_line = candidates[0]

            if best_score < 2:
                return None

            cleaned = re.sub(r'\b(SIRET|SIREN|TVA|RC|Matricule|N[oº]+)\b[:\s]*\S*', '', best_line, flags=re.I)
            cleaned = re.sub(r'[^\w\s\-\.,&()\/]', '', cleaned).strip()
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
            r'(\d{7}[A-Z]{3}\d{3})',
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
                amount_str = re.sub(r'[^\d.]', '', amount_str)
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def _extract_type_achat(self, text: str) -> str:
        """Extract purchase type"""
        if text is None or not isinstance(text, str) or not text.strip():
            return "Article"
            
        types = {
            'Article': ['article', 'produit', 'matériel', 'matériau', 'équipement', 'fourniture'],
            'Service': ['service', 'prestation', 'consultation', 'maintenance'],
            'CAPEX': ['capex', 'investissement', 'immobilisation', 'capital'],
            'Contrat': ['contrat', 'abonnement', 'subscription'],
        }
        
        try:
            for type_name, keywords in types.items():
                if any(keyword in text.lower() for keyword in keywords):
                    return type_name
        except (AttributeError, TypeError):
            pass
        
        return "Article"
    
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
        """Extract unit"""
        if text is None or not isinstance(text, str):
            return "pcs"
            
        units = ['pcs', 'pièce', 'pièces', 'piéces', 'kg', 'litre', 'mètre', 'metre', 'heure', 'jour', 'unit', 'unité']
        
        try:
            for unit in units:
                if unit in text.lower():
                    if unit in ['pcs', 'pièce', 'pièces', 'piéces', 'unit', 'unité']:
                        return "pcs"
                    return unit
        except (AttributeError, TypeError):
            pass
        
        return "pcs"
    
    def _extract_specifications(self, text: str) -> Optional[str]:
        """Extract technical specifications"""
        if not text:
            return None
            
        patterns = [
            r'(?:Description|Spécifications|Specifications|Details|Détails)\s*[:.]?\s*(.{20,200})',
            r'(?:Caractéristiques|Features|Reference|Référence)\s*[:.]?\s*(.{20,200})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                spec_text = match.group(1).strip()
                spec_text = re.sub(r'\s+', ' ', spec_text)
                return spec_text[:200]
        return None
    
    def _call_llm_map_fields(self, raw_text: str) -> Dict:
        """LLM-assisted field mapping"""
        RAPIDAPI_URL = os.getenv("RAPIDAPI_URL")
        RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
        RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

        if not RAPIDAPI_URL or not RAPIDAPI_KEY:
            logger.warning("⚠️ RapidAPI URL/KEY not set; skipping LLM mapping.")
            return {}

        system_prompt = (
            "You are a JSON extractor. Given raw OCR text of an invoice in French or English, "
            "strictly return a JSON object (no explanatory text) with the following keys: "
            "numero_facture, date_facture, fournisseur_nom, fournisseur_matricule, numero_po, "
            "montant_ht, montant_tva, montant_ttc, devise, type_achat, quantite, unite, "
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

        try:
            data = resp.json()
        except ValueError:
            raw = resp.text
            m = _re_for_json.search(r'(\{[\s\S]*\})', raw)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
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

                expected_keys = {
                    "numero_facture", "date_facture", "fournisseur_nom",
                    "fournisseur_matricule", "numero_po", "montant_ht",
                    "montant_tva", "montant_ttc", "devise", "type_achat",
                    "quantite", "unite", "specifications_techniques"
                }
                if expected_keys & set(data.keys()):
                    return data

        except Exception as e:
            logger.debug(f"🔎 Error while trying to interpret LLM JSON: {e}")

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

        logger.warning("⚠️ LLM returned no parseable JSON mapping.")
        return {}


def process_facture_from_bytes(image_bytes: bytes) -> Dict:
    """Complete workflow: Extract invoice data from image or PDF bytes"""
    ocr = FactureOCREasyOCR(languages=['fr', 'en'])
    result = ocr.extract_from_bytes(image_bytes)
    
    if result.get("success"):
        logger.info(f"✅ Invoice extraction completed")
        logger.info(f"   Numero: {result.get('numero_facture')}")
        logger.info(f"   Fournisseur: {result.get('fournisseur_nom')}")
        logger.info(f"   Montant TTC: {result.get('montant_ttc')} {result.get('devise')}")
    else:
        logger.error(f"❌ Extraction failed: {result.get('error')}")
    
    return result


def process_facture_from_file(file_path: str) -> Dict:
    """Complete workflow: Extract invoice data from image or PDF file"""
    ocr = FactureOCREasyOCR(languages=['fr', 'en'])
    result = ocr.extract_from_file(file_path)
    
    if result.get("success"):
        logger.info(f"✅ Invoice extraction completed")
        logger.info(f"   Numero: {result.get('numero_facture')}")
        logger.info(f"   Fournisseur: {result.get('fournisseur_nom')}")
        logger.info(f"   Montant TTC: {result.get('montant_ttc')} {result.get('devise')}")
    else:
        logger.error(f"❌ Extraction failed: {result.get('error')}")
    
    return result