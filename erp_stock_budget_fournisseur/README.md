# ERP System - MongoDB Edition 🏢

Système ERP complet avec gestion des fournisseurs, contrôle budgétaire et gestion de stock intégrée à **MongoDB Atlas** (base de données cloud).

## 🎯 Fonctionnalités

### 1️⃣ Gestion Fournisseurs (BPMN Process 1)
- ✅ Création de demandes fournisseurs
- ✅ Contrôle automatique des doublons (tax_id unique)
- ✅ Vérification de conformité
- ✅ Workflow de validation (PENDING → ACTIVE)

### 2️⃣ Contrôle Budgétaire (BPMN Process 2)
- ✅ Vérification automatique de disponibilité budgétaire
- ✅ Règles métier configurables (seuils d'approbation)
- ✅ Mise à jour en temps réel des budgets
- ✅ Historique des transactions

### 3️⃣ Stock & Comptabilité (BPMN Process 3)
- ✅ Réception/Sortie de marchandises
- ✅ Génération automatique d'écritures comptables
- ✅ Imputation des coûts par projet
- ✅ Alertes stock faible

## 📋 Prérequis

### Installation

**Python 3.10+ requis**

```powershell
# Vérifier la version Python
python --version
```

✅ **Avantages MongoDB:**
- Base de données cloud (MongoDB Atlas)
- Scalabilité horizontale
- Support des données non structurées
- Index automatiques pour performance

## 🚀 Installation

### 1. Cloner/Naviguer vers le projet
```powershell
cd "C:\Users\Mega Pc\Desktop\erp islem"
```

### 2. Créer un environnement virtuel
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances
```powershell
pip install -r requirements.txt
```

### 4. Configuration MongoDB

#### Créer le fichier .env (optionnel)
```powershell
# Créer un fichier .env si vous voulez personnaliser la connexion
```

#### Configuration par défaut
Le système utilise déjà la connexion MongoDB Atlas configurée:
```env
MONGO_URI=mongodb+srv://medhelaliamin125_db_user:aUfXpfkyHbpynyKL@erp.yrgvgdj.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=erp_system
```

✅ **La base de données sera créée automatiquement lors du premier démarrage.**

## ▶️ Démarrage

### Méthode 1: Scripts PowerShell (Recommandé)

**Terminal 1 - Backend:**
```powershell
.\start_backend.ps1
```

**Terminal 2 - Frontend:**
```powershell
.\start_frontend.ps1
```

### Méthode 2: Commandes manuelles

**Terminal 1 - Backend:**
```powershell
.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --port 8000
```

Accès:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Terminal 2 - Frontend:**
```powershell
.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Accès:
- Interface: http://localhost:8501

## 📁 Structure du Projet

```
erp islem/
│
├── backend/
│   ├── main.py                 # Application FastAPI principale
│   ├── models.py               # Modèles Pydantic pour validation
│   ├── routes_suppliers.py     # Routes fournisseurs (MongoDB)
│   ├── routes_budget.py        # Routes budget (MongoDB)
│   └── routes_stock.py         # Routes stock (MongoDB)
│
├── frontend/
│   └── app.py                  # Interface Streamlit
│
├── config/
│   └── database.py             # Configuration MongoDB
│
├── .env                        # Variables d'environnement (optionnel)
├── requirements.txt            # Dépendances Python
├── start_backend.ps1          # Script de démarrage backend
├── start_frontend.ps1          # Script de démarrage frontend
└── README.md                   # Ce fichier
```

## 🗄️ Collections MongoDB

Le système crée automatiquement les collections suivantes dans la base de données `erp_system`:

- `suppliers` - Fournisseurs
- `budgets` - Budgets départementaux
- `budget_transactions` - Transactions budgétaires
- `pending_transactions` - Transactions en attente de validation
- `stock` - Articles en stock
- `stock_movements` - Mouvements de stock
- `accounting_journal` - Journal comptable
- `projects` - Projets

## 📊 Index MongoDB (Auto-créés)

Les index suivants sont créés automatiquement pour optimiser les performances:

- `suppliers.tax_id` (unique)
- `suppliers.status`
- `budgets.department` (unique)
- `budget_transactions.department`
- `budget_transactions.created_at`
- `pending_transactions.department`
- `pending_transactions.status`
- `stock.item_id` (unique)
- `stock_movements.item_id`
- `stock_movements.created_at`
- `accounting_journal.date`
- `projects.project_id` (unique)

## 🔧 Tests de l'API

### Créer un fournisseur
```bash
curl -X POST "http://localhost:8000/suppliers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "tax_id": "123456789",
    "category": "IT",
    "email": "contact@acme.com"
  }'
```

### Vérifier le budget
```bash
curl -X POST "http://localhost:8000/budget/check" \
  -H "Content-Type: application/json" \
  -d '{
    "department": "IT",
    "amount": 5000,
    "description": "Achat serveurs"
  }'
```

### Réception de stock
```bash
curl -X POST "http://localhost:8000/stock/receive" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "REF-001",
    "quantity": 100,
    "unit_price": 25.5,
    "movement_type": "IN",
    "project_id": "PRJ-ALPHA"
  }'
```

## 📝 Initialisation des Données

### Créer des budgets de test
```bash
curl -X POST "http://localhost:8000/budget/" \
  -H "Content-Type: application/json" \
  -d '{"department": "IT", "allocated": 50000, "used": 0}'

curl -X POST "http://localhost:8000/budget/" \
  -H "Content-Type: application/json" \
  -d '{"department": "Marketing", "allocated": 30000, "used": 0}'

curl -X POST "http://localhost:8000/budget/" \
  -H "Content-Type: application/json" \
  -d '{"department": "Operations", "allocated": 100000, "used": 0}'
```

## 🛠️ Commandes Utiles

### Vérifier la connexion MongoDB
```powershell
# Le health check de l'API vérifie automatiquement la connexion
curl http://localhost:8000/health
```

### Voir les statistiques
```powershell
curl http://localhost:8000/stats
```

### Accéder à MongoDB Atlas
1. Connectez-vous à [MongoDB Atlas](https://cloud.mongodb.com)
2. Naviguez vers votre cluster `erp.yrgvgdj.mongodb.net`
3. Sélectionnez la base de données `erp_system`
4. Explorez les collections et documents

## 🐛 Dépannage

### Erreur: Connexion MongoDB échouée
```powershell
# Vérifier la connexion internet
ping erp.yrgvgdj.mongodb.net

# Vérifier les variables d'environnement
# Le MONGO_URI est déjà configuré dans config/database.py
```

### Erreur: Backend non accessible
```powershell
# Vérifier le port
netstat -ano | findstr :8000

# Relancer le backend
uvicorn backend.main:app --reload
```

### Erreur: Import modules
```powershell
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Erreur: Motor/Pymongo non installé
```powershell
# Installer manuellement
pip install motor pymongo
```

## 🔐 Sécurité

⚠️ **Important:** Le fichier `config/database.py` contient les credentials MongoDB. En production:
- Utilisez des variables d'environnement
- Ne commitez jamais les credentials dans le code
- Utilisez des secrets managers (Azure Key Vault, AWS Secrets Manager, etc.)

## 📈 Évolutions Futures

- [ ] Authentification JWT
- [ ] Gestion multi-utilisateurs
- [ ] Notifications en temps réel
- [ ] Export PDF des rapports
- [ ] Dashboard analytics avancé
- [ ] API GraphQL
- [ ] Tests unitaires
- [ ] Déploiement Docker
- [ ] Migration de données depuis SQLite

## 👨‍💻 Développement

### Lancer en mode debug
```powershell
# Backend
uvicorn backend.main:app --reload --log-level debug

# Frontend
streamlit run frontend/app.py --server.runOnSave true
```

### Structure des Documents MongoDB

#### Document Supplier (exemple)
```json
{
  "_id": ObjectId("..."),
  "id": "SUP-ABC12345",
  "name": "Acme Corp",
  "tax_id": "123456789",
  "category": "IT",
  "email": "contact@acme.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "status": "ACTIVE",
  "compliance_checked": true,
  "rejection_reason": null,
  "created_at": ISODate("2025-01-01T00:00:00Z"),
  "updated_at": ISODate("2025-01-01T00:00:00Z")
}
```

## 📄 Licence

MIT License

## 🤝 Contact

Pour toute question ou suggestion, contactez l'équipe de développement.

---

**Version:** 4.0.0 (MongoDB Edition)  
**Dernière mise à jour:** Janvier 2025  
**Base de données:** MongoDB Atlas  
**Database Name:** erp_system
