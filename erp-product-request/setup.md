# Terminal 1: Backend
cd backend
uvicorn backend_pr:app --reload --port 8050

# Terminal 2: Frontend
cd frontend
streamlit run main_pr.py

# Run this to test your email config
python backend/email_service.py