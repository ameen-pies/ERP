ERP.docx# Mini ERP - GRN Module

A mini ERP system for managing Purchase Orders (PO) and Goods Receipt Notes (GRN) with a FastAPI backend and Streamlit frontend.

## Prerequisites

- Python 3.8 or higher
- MongoDB connection (already configured in the project)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## How to Run the Project

### Step 1: Start the Backend Server

Open a terminal and run:
```bash
uvicorn backend.main:app --reload
```

The FastAPI backend will start on `http://localhost:8000`

You can also access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 2: Start the Frontend Application

Open a **new terminal** (keep the backend running) and run:
```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit frontend will start and automatically open in your browser at `http://localhost:8501`

## Usage

1. Make sure both the backend and frontend are running
2. Access the application through the Streamlit interface (usually opens automatically)
3. Use the sidebar navigation to access different features:
   - **Dashboard**: View database overview and supplier directory
   - **Create PO**: Create new Purchase Orders
   - **Create GRN**: Create Goods Receipt Notes
   - **Stock Ledger**: View stock movements
   - **View Disputes**: View disputes and anomalies

## Notes

- The backend must be running before starting the frontend
- The frontend connects to the backend API at `http://localhost:8000/api`
- The backend automatically seeds demo data on startup
- MongoDB connection is pre-configured in the project




now change the way you load the GRNs in dashboard and make it take the reference PO from the GRN directly to enhance performance, and when creating a GRN make sure to add the PO reference to the GRN document too