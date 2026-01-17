# ERP Purchase model

> A comprehensive enterprise resource planning system with integrated modules for purchase management, approval workflows, and document processing.

---

## 📋 Table of Contents

- System Architecture
- [Installation](#-installation)
- [Module Execution](#-module-execution)
- [System Architecture](#-system-architecture)
- [Default Users](#-default-users)
- [Tech Stack](#%EF%B8%8F-tech-stack)
- [Troubleshooting](#-troubleshooting)

---


## System Architecture

| Module | Purpose | Port(s) |
|--------|---------|---------|
| **Login** | Authentication & Dashboard | `8501` |
| **Product Request** | PR Creation & Management | `8050` |
| **Purchase Order** | PO Generation & Tracking | `8000` |
| **Approval Workflow** | Multi-level Validations | `8001` |
| **Facturation** | Invoice OCR & Processing | `8000` |
| **GRN** | Goods Receipt & Disputes | `8000/8501` |
| **Stock-Budget** | Inventory & Finance Control | `8000/8501` |

## Installation

### 1️⃣ Clone Repository
```bash
it clone https://github.com/ameen-pies/ERP
cd ERP
```

### 2️⃣ Setup Virtual Environment
```bash
# Create environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Configure Environment

Create `.env` file in root:
```env
MONGODB_URI=your_mongodb_atlas_connection_string
MONGO_DB_NAME=purchase_request
```

---

## 🎯 Module Execution

### 🔐 Login Module (first page)
```bash
cd login
streamlit run app.py
```

**Access:** [`http://localhost:8501`](http://localhost:8501)

---

### 📝 Purchase Request Module
```bash
cd erp-product-request/backend
python main_pr.py
```

**Access:** [`http://localhost:8050`](http://localhost:8050)

---

### 🛒 Purchase Order Module
```bash
cd erp-purchase-order
python main.py
```

**Access:** [`http://localhost:8000`](http://localhost:8000)

---

### ✅ Approval Workflow Module
```bash
cd erp-approval-workflow
python main.py
```

**API:** [`http://localhost:8001`](http://localhost:8001)  
**UI:** [`http://localhost:8001/ui.html`](http://localhost:8001/ui.html)

---

### 🧾 Invoice Processing Module
```bash
cd erp-facturation
python app.py
```

**Access:** [`http://localhost:8000`](http://localhost:8000)

---

### 📦 GRN Module
```bash
cd erp-GRN

# Terminal 1 - API
uvicorn main:app --reload

# Terminal 2 - UI
streamlit run streamlit_app.py
```

**API:** [`http://localhost:8000`](http://localhost:8000)  
**UI:** [`http://localhost:8501`](http://localhost:8501)

---

### 📊 Stock & Budget Module
```bash
cd erp_stock_budget_fournisseur

# Terminal 1
.\start_backend.ps1

# Terminal 2
.\start_frontend.ps1
```

**API:** [`http://localhost:8000`](http://localhost:8000)  
**UI:** [`http://localhost:8501`](http://localhost:8501)

---
### Access the Integrated Platform

Once all modules are running, open the unified platform:
```bash
cd login
# Open index.html in your browser
start index.html          # Windows
open index.html           # Mac
xdg-open index.html       # Linux
```

**Or access directly:** [`login/index.html`](login/index.html)

---

## 👥 Default Users

| Role | Access Level |
|------|-------------|
| **User** | Department User - Create Requests |
| **Head** | Department Head - Approve Requests |
| **Treasurer** | Financial Approver - Budget Control |
| **Admin** | System Administrator - Full Access |

---

## 🛠️ Tech Stack

**Backend**
- FastAPI
- Python 3.10+
- Motor (MongoDB async driver)

**Frontend**
- Streamlit
- HTML/CSS/JavaScript
- Plotly

**Database**
- MongoDB Atlas

**AI/ML**
- EasyOCR (Invoice Processing)

**Workflow Engine**
- Custom approval system
---

## 🎥 Demo

See **`Demo video.mp4`** for complete system walkthrough

---

<div align="center">

**The ERP purchase model**

</div>
