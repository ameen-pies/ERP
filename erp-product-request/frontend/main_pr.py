import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="ERP Achat - Purchase Requests", layout="wide")

# Styling
PRIMARY_COLOR = "#1E3A8A"
SUCCESS_COLOR = "#10b981"
WARNING_COLOR = "#f59e0b"
DANGER_COLOR = "#ef4444"

st.markdown(f"""
<style>
    .stButton>button {{
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {{
        border-radius: 6px;
    }}
    .status-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .status-brouillon {{ background-color: #e5e7eb; color: #374151; }}
    .status-validation {{ background-color: #fef3c7; color: #92400e; }}
    .status-validee {{ background-color: #dbeafe; color: #1e40af; }}
    .status-active {{ background-color: #d1fae5; color: #065f46; }}
    .status-rejetee {{ background-color: #fee2e2; color: #991b1b; }}
    .status-archivee {{ background-color: #f3f4f6; color: #6b7280; }}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8050"

# Sidebar
st.sidebar.title("🏢 ERP Achat")
st.sidebar.markdown("### Module de Requêtes d'Achat")

page = st.sidebar.radio("Navigation", [
    "📝 Créer une PR",
    "📋 Liste des PRs",
    "📊 Tableau de bord"
])

# Helper function for status badges
def status_badge(statut):
    status_map = {
        "Brouillon": "brouillon",
        "En validation hiérarchique": "validation",
        "Validée": "validee",
        "Active": "active",
        "Rejetée": "rejetee",
        "Archivée": "archivee"
    }
    css_class = status_map.get(statut, "brouillon")
    return f'<span class="status-badge status-{css_class}">{statut}</span>'

# Dynamic fields based on purchase type
def get_dynamic_fields(type_achat):
    fields = {}
    if type_achat in ["Article", "CAPEX"]:
        fields["specifications_techniques"] = st.text_area(
            "Spécifications techniques *",
            help="Décrivez les spécifications détaillées du produit"
        )
    elif type_achat == "Service":
        fields["description_service"] = st.text_area(
            "Description du service *",
            help="Décrivez le service requis"
        )
    elif type_achat == "Contrat":
        fields["duree_contrat"] = st.text_input(
            "Durée du contrat *",
            help="Ex: 12 mois, 2 ans"
        )
    elif type_achat == "Catalogue":
        fields["reference_catalogue"] = st.text_input(
            "Référence catalogue *",
            help="Numéro de référence du catalogue"
        )
    return fields

# ==================== PAGE: CREATE PR ====================
if page == "📝 Créer une PR":
    st.title("📝 Créer une Requête d'Achat (PR)")
    st.markdown("---")
    
    with st.form("pr_form", clear_on_submit=True):
        st.subheader("1️⃣ Identification du demandeur")
        col1, col2 = st.columns(2)
        with col1:
            demandeur = st.text_input("Nom du demandeur *", placeholder="Jean Dupont")
            email_demandeur = st.text_input("Email demandeur *", placeholder="jean.dupont@company.com")
        with col2:
            manager_email = st.text_input("Email Manager *", placeholder="manager@company.com", 
                                         help="Le manager recevra un email pour validation hiérarchique")
            finance_email = st.text_input("Email Finance *", placeholder="finance@company.com",
                                         help="Le service finance recevra un email pour validation budgétaire")
        
        st.markdown("---")
        st.subheader("2️⃣ Description du besoin")
        
        col1, col2 = st.columns(2)
        with col1:
            type_achat = st.selectbox(
                "Type d'achat *",
                ["Article", "Service", "CAPEX", "Contrat", "Catalogue"]
            )
        with col2:
            priorite = st.selectbox("Priorité", ["Haute", "Moyenne", "Basse"])
        
        details = st.text_area(
            "Détails de la demande *",
            placeholder="Décrivez précisément votre besoin...",
            height=100
        )
        
        # Dynamic fields based on type
        dynamic_fields = get_dynamic_fields(type_achat)
        
        st.markdown("---")
        st.subheader("3️⃣ Informations complémentaires")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            quantite = st.number_input("Quantité", min_value=1, value=1)
        with col2:
            unite = st.text_input("Unité", placeholder="pièce, kg, heure...")
        with col3:
            prix_estime = st.number_input("Prix estimé (TND)", min_value=0.0, step=10.0)
        
        col1, col2 = st.columns(2)
        with col1:
            centre_cout = st.text_input("Centre de coût", placeholder="CC-001")
            fournisseur_suggere = st.text_input("Fournisseur suggéré", placeholder="Nom du fournisseur")
        with col2:
            delai_souhaite = st.text_input("Délai souhaité", placeholder="Ex: 2 semaines, urgent")
            justification = st.text_area("Justification", placeholder="Pourquoi ce besoin?", height=80)
        
        st.markdown("---")
        st.subheader("4️⃣ Documents")
        uploaded_files = st.file_uploader(
            "Joindre des documents",
            accept_multiple_files=True,
            help="Devis, spécifications, photos..."
        )
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_draft = st.form_submit_button("💾 Sauvegarder (Brouillon)", use_container_width=True)
        with col2:
            submit_validate = st.form_submit_button("✅ Créer et Soumettre", use_container_width=True, type="primary")
    
    if submit_draft or submit_validate:
        if not all([demandeur, email_demandeur, manager_email, finance_email, details]):
            st.error("⚠️ Veuillez remplir tous les champs obligatoires (*)")
        else:
            # Prepare form data
            form_data = {
                "demandeur": demandeur,
                "email_demandeur": email_demandeur,
                "manager_email": manager_email,
                "finance_email": finance_email,
                "type_achat": type_achat,
                "details": details,
                "quantite": str(quantite),
                "unite": unite if unite else "",
                "prix_estime": str(prix_estime),
                "fournisseur_suggere": fournisseur_suggere if fournisseur_suggere else "",
                "centre_cout": centre_cout if centre_cout else "",
                "priorite": priorite,
                "delai_souhaite": delai_souhaite if delai_souhaite else "",
                "justification": justification if justification else ""
            }
            
            # Add dynamic fields
            for key, value in dynamic_fields.items():
                if value:
                    form_data[key] = value
            
            # Prepare files for upload
            files_data = []
            if uploaded_files:
                for f in uploaded_files:
                    files_data.append(("files", (f.name, f.getvalue(), f.type)))
            
            try:
                # Create PR
                response = requests.post(
                    f"{API_URL}/pr/",
                    data=form_data,
                    files=files_data if files_data else None
                )
                
                if response.status_code == 200:
                    result = response.json()
                    pr_id = result["pr_id"]
                    
                    st.success(f"✅ PR créée avec succès! ID: **{pr_id}**")
                    
                    # If submit for validation
                    if submit_validate:
                        submit_response = requests.post(f"{API_URL}/pr/{pr_id}/submit")
                        if submit_response.status_code == 200:
                            st.success(f"📧 PR soumise pour validation hiérarchique. Email envoyé à {manager_email}")
                        else:
                            st.warning("PR créée mais erreur lors de la soumission")
                    else:
                        st.info("💾 PR sauvegardée en brouillon. Vous pouvez la soumettre plus tard.")
                else:
                    st.error(f"❌ Erreur: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"❌ Erreur de connexion: {str(e)}")

# ==================== PAGE: LIST PRs ====================
elif page == "📋 Liste des PRs":
    st.title("📋 Liste des Requêtes d'Achat")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        filter_statut = st.selectbox(
            "Filtrer par statut",
            ["Tous", "Brouillon", "En validation hiérarchique", "Validée", "Active", "Rejetée", "Archivée"]
        )
    with col3:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    try:
        # Fetch PRs
        params = {}
        if filter_statut != "Tous":
            params["statut"] = filter_statut
        
        response = requests.get(f"{API_URL}/pr/", params=params)
        
        if response.status_code == 200:
            prs = response.json()
            
            if not prs:
                st.info("📭 Aucune PR trouvée")
            else:
                st.write(f"**{len(prs)} PR(s) trouvée(s)**")
                
                for pr in prs:
                    with st.expander(
                        f"🔹 PR-{pr['id']} | {pr['type_achat']} | {pr['demandeur']} | "
                        f"{pr.get('prix_estime', 0):.2f} TND"
                    ):
                        # Status badge
                        st.markdown(status_badge(pr['statut']), unsafe_allow_html=True)
                        
                        # Details in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Demandeur:** {pr['demandeur']}")
                            st.write(f"**Type:** {pr['type_achat']}")
                            st.write(f"**Priorité:** {pr.get('priorite', '-')}")
                        with col2:
                            st.write(f"**Centre de coût:** {pr.get('centre_cout', '-')}")
                            st.write(f"**Quantité:** {pr.get('quantite', '-')} {pr.get('unite', '')}")
                            st.write(f"**Prix estimé:** {pr.get('prix_estime', 0):.2f} TND")
                        with col3:
                            date_creation = datetime.fromisoformat(pr['date_creation']).strftime("%d/%m/%Y %H:%M")
                            st.write(f"**Créée le:** {date_creation}")
                            st.write(f"**Délai:** {pr.get('delai_souhaite', '-')}")
                            st.write(f"**Fournisseur:** {pr.get('fournisseur_suggere', '-')}")
                        
                        st.markdown("**Détails:**")
                        st.write(pr['details'])
                        
                        if pr.get('justification'):
                            st.markdown("**Justification:**")
                            st.write(pr['justification'])
                        
                        # Documents
                        if pr.get('documents'):
                            st.markdown("**Documents joints:**")
                            for doc in pr['documents']:
                                st.write(f"📎 {doc['filename']}")
                        
                        # History
                        st.markdown("**Historique:**")
                        for h in pr['history']:
                            timestamp = datetime.fromisoformat(h['timestamp']).strftime("%d/%m/%Y %H:%M")
                            approved_text = ""
                            if 'approved' in h:
                                approved_text = " ✅" if h['approved'] else " ❌"
                            st.write(f"- {timestamp} | {h['action']} par {h['user']}{approved_text}")
                        
                        # Actions
                        st.markdown("---")
                        action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
                        
                        with action_col1:
                            if pr['statut'] == "Brouillon":
                                if st.button(f"📤 Soumettre PR-{pr['id']}", key=f"submit_{pr['id']}"):
                                    resp = requests.post(f"{API_URL}/pr/{pr['id']}/submit")
                                    if resp.status_code == 200:
                                        st.success("✅ PR soumise!")
                                        st.rerun()
                        
                        with action_col2:
                            if pr['statut'] in ["Active", "Rejetée"]:
                                if st.button(f"📦 Archiver PR-{pr['id']}", key=f"archive_{pr['id']}"):
                                    resp = requests.post(
                                        f"{API_URL}/pr/{pr['id']}/archive",
                                        data={"user": pr['demandeur']}
                                    )
                                    if resp.status_code == 200:
                                        st.success("✅ PR archivée!")
                                        st.rerun()
        else:
            st.error("❌ Erreur lors de la récupération des PRs")
    except Exception as e:
        st.error(f"❌ Erreur de connexion: {str(e)}")

# ==================== PAGE: DASHBOARD ====================
elif page == "📊 Tableau de bord":
    st.title("📊 Tableau de Bord - PRs")
    
    try:
        response = requests.get(f"{API_URL}/pr/")
        if response.status_code == 200:
            prs = response.json()
            
            # Statistics
            total = len(prs)
            brouillon = len([p for p in prs if p['statut'] == "Brouillon"])
            en_validation = len([p for p in prs if p['statut'] == "En validation hiérarchique"])
            validee = len([p for p in prs if p['statut'] == "Validée"])
            active = len([p for p in prs if p['statut'] == "Active"])
            rejetee = len([p for p in prs if p['statut'] == "Rejetée"])
            archivee = len([p for p in prs if p['statut'] == "Archivée"])
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total PRs", total)
            with col2:
                st.metric("Brouillon", brouillon)
            with col3:
                st.metric("En validation", en_validation)
            with col4:
                st.metric("Active", active)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Validée", validee)
            with col2:
                st.metric("Rejetée", rejetee)
            with col3:
                st.metric("Archivée", archivee)
            with col4:
                total_montant = sum([p.get('prix_estime', 0) for p in prs if p.get('prix_estime')])
                st.metric("Montant total", f"{total_montant:.2f} TND")
            
            st.markdown("---")
            
            # Recent PRs
            st.subheader("🕒 PRs Récentes")
            recent_prs = sorted(prs, key=lambda x: x['date_creation'], reverse=True)[:5]
            
            for pr in recent_prs:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.write(f"**PR-{pr['id']}**")
                with col2:
                    st.write(pr['demandeur'])
                with col3:
                    st.markdown(status_badge(pr['statut']), unsafe_allow_html=True)
                with col4:
                    st.write(f"{pr.get('prix_estime', 0):.0f} TND")
        else:
            st.error("❌ Erreur lors de la récupération des données")
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**ERP Achat v1.0**")
st.sidebar.markdown("Développé pour la gestion des PRs")