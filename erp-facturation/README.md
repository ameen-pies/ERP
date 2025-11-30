erp-achat-invoice/
│
├── backend/
│   ├── __init__.py
│   ├── invoice_app.py              # FastAPI (PRs + Invoices)
│   ├── invoice_models.py          
│   ├── invoice_ocr.py              # Service OCR extraction
│   ├── invoice_api.py              # Routes API factures
│   ├── db.py                     
│   └── email_service.py            # email notifications
│
├── frontend/
│   ├── __init__.py
│   ├── main.py                     # Interface Streamlit PRs
│   └── invoice_main.py             # Interface Streamlit Factures
│
├── .env                            # Configuration environment
├── requirements.txt
└── setup.md                         # Script démarrage

=========================================================
DÉTAILS DES FICHIERS
=========================================================

backend/invoice_ocr.py
----------------------
- extract_invoice_data(file_bytes, file_type) -> OCRData
  * Utilise Tesseract/Google Vision/AWS Textract
  * Extrait: numero_facture, date_facture, fournisseur, montants, etc.
  * Retourne confidence score

- extract_line_items(text) -> List[LigneFacture]
  * Parse les lignes de la facture
  * Extrait quantité, prix unitaire, montants



- validate_invoice_against_pr(invoice_data, pr_id) -> ValidationResult
  * Récupère la PR depuis MongoDB
  * Compare:
    - Fournisseur (nom, SIRET)
    - Montant total (tolérance ±5%)
    - Quantité
    - Description/référence
  * Génère erreurs, warnings, confidence_score

- check_fiscal_compliance(invoice_data) -> bool
  * Vérifie conformité fiscale tunisienne
  * TVA, SIRET, mentions obligatoires

backend/invoice_api.py
----------------------
Routes API:

POST /invoices/upload
- Upload fichier (PDF/Image)
- Extraction OCR
- Demande PR_ID pour validation
- Sauvegarde dans collection "factures"

GET /invoices/
- Liste factures (filtres: statut, fournisseur, dates)

GET /invoices/{invoice_id}
- Détails facture + historique

POST /invoices/{invoice_id}/validate-with-pr
- Valider facture contre PR spécifique
- Mise à jour statut

POST /invoices/{invoice_id}/approve
- Approuver pour paiement

POST /invoices/{invoice_id}/reject
- Rejeter avec raison

GET /invoices/stats/summary
- Statistiques tableau de bord


backend/invoice_models.py (UPDATED)
------------------------------------
Classes:

- StatutFacture (Enum)
  * RECUE, EN_ANALYSE, VALIDEE_CONTRE_PR, 
  * EN_ATTENTE_CORRECTION, APPROUVEE, REJETEE, PAYEE

- OCRData
  * Données extraites par OCR
  * confidence: float

- PRMatchResult
  * pr_id: str
  * matched: bool
  * differences: List[Dict]
  * confidence_score: float

- Facture (Pydantic Model)
  * Tous les champs facture
  * pr_match_result: Optional[PRMatchResult]
  * validation_result: ValidationResult


backend/db.py (UPDATED)
-----------------------
Ajouter:

facture_collection = db["factures"]

def get_facture_collection():
    return facture_collection

Indexes:
- facture_collection.create_index("id", unique=True)
- facture_collection.create_index("numero_facture")
- facture_collection.create_index("pr_id")
- facture_collection.create_index("statut")


frontend/invoice_main.py (UPDATED)
-----------------------------------
Tabs:

1. 📤 Réception Facture
   - Upload fichier
   - Saisie PR_ID manuel
   - Extraction OCR automatique
   - Affichage données extraites
   - Validation contre PR
   - Affichage résultats comparaison

2. 📋 Liste des Factures
   - Table avec filtres
   - Statut coloré
   - Actions rapides

3. 📊 Tableau de Bord
   - KPIs: Total factures, en attente, montant
   - Répartition par statut
   - Conformité PR (%)
   - Délai moyen traitement

4. 🔍 Recherche Avancée
   - Multi-critères
   - Export Excel/CSV

=========================================================
FLUX DE TRAITEMENT FACTURE
=========================================================

1. UPLOAD
   ↓
2. EXTRACTION OCR
   - Scan document
   - Extraire texte + structure
   - Parser champs clés
   ↓
3. DEMANDE PR_ID
   - Utilisateur saisit PR_ID
   ↓
4. VALIDATION CONTRE PR
   - Récupérer PR depuis MongoDB
   - Comparer champs:
     * Fournisseur ✓
     * Montant total (±5%) ✓
     * Quantité ✓
     * Description/Référence ✓
   - Calculer confidence_score
   ↓
5. RÉSULTAT VALIDATION
   - Afficher différences
   - Statut: VALIDEE_CONTRE_PR ou EN_ATTENTE_CORRECTION
   ↓
6. SAUVEGARDE
   - Collection: purchase_requests.factures
   - Lien vers PR via pr_id
   ↓
7. NOTIFICATIONS
   - Email comptabilité
   - Email demandeur PR