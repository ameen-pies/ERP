conda activate clustering

# Terminal 1: Backend API
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
# or python app.py

# Terminal 2: Frontend PRs
cd frontend
streamlit run main.py --server.port 8501

# Terminal 3: Frontend Factures
cd frontend
streamlit run facture_ui.py --server.port 8502