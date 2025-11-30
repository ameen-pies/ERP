# Structure du projet

erp_module_achat/
│
├─ main.py              # Streamlit app : interface moderne et sidebar
├─ backend/
│   ├─ fastapi_app.py   # FastAPI API : endpoints CRUD + workflow
│   ├─ models.py        # Pydantic models pour PR
│   ├─ db.py            # Dict temporaire pour PR
│   └─ utils.py         # Fonctions utilitaires (validation, notifications)
├─ frontend/
│   └─ styles.py        # Couleurs, boutons arrondis, etc.
└─ requirements.txt     # streamlit, fastapi, uvicorn, pymongo, etc.


## RP workflow 

1. Création PR (demandeur)

2. Validation hiérarchique (manager)

3. Validation budgétaire (finance)

4. Notifications simulées (log console)

5. Frontend Streamlit moderne (liste PR, actions manager/finance, upload fichiers)