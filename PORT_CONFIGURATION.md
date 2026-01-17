# ERP Platform - Port Configuration

## Main Entry Point
- **Login/Dashboard**: Streamlit on port 8501 (default)
  - Access: http://localhost:8501
  - File: `login/app.py`

## Module Ports

### Backend services (FastAPI)
1. **Purchase Order Backend**: Port 8000
   - Access: http://localhost:8000
   - File: `erp-purchase-order/main.py`
   - API Documentation: http://localhost:8000/docs

2. **Approval Workflow Backend**: Port 8001
   - Access: http://localhost:8001
   - File: `erp-approval-workflow/main.py`
   - UI: http://localhost:8001/ui.html

3. **Stock/Budget/Suppliers Backend**: Port 8000
   - Access: http://localhost:8000
   - File: `erp_stock_budget_fournisseur/backend/main.py`
   - Note: Conflicts with Purchase Order backend - use different port if running simultaneously

4. **Facturation Backend**: Port 8000
   - Access: http://localhost:8000
   - File: `erp-facturation/backend/app.py`
   - Note: Conflicts with other backends - use different port if running simultaneously

### Frontend services (Streamlit)
1. **Product Request**: Port 8502
   - Access: http://localhost:8502
   - File: `erp-product-request/frontend/main_pr.py`

2. **GRN (Goods Receipt Notes)**: Port 8503
   - Access: http://localhost:8503
   - File: `erp-GRN/frontend/streamlit_app.py`

3. **Facturation (Receipt Scanning)**: Port 8504
   - Access: http://localhost:8504
   - File: `erp-facturation/frontend/main.py`

4. **Suppliers Database**: Port 8505
   - Access: http://localhost:8505
   - File: `erp_stock_budget_fournisseur/frontend/app.py`

### Static HTML Server
- **HTTP Server**: Port 5500
   - Access: http://localhost:5500
   - File: `runserver.py`
   - Serves: `erp-purchase-order/index.html` at http://localhost:5500/erp-purchase-order/

## Module links in dashboard

The main dashboard (`login/Index.html`) links to modules as follows:

- **Purchase Request**: http://localhost:8502
- **Purchase Order**: http://localhost:5500/erp-purchase-order/
- **Approval Workflow**: http://localhost:8001/ui.html
- **GRN**: http://localhost:8503
- **Facturation**: http://localhost:8504
- **Suppliers Database**: http://localhost:8505
