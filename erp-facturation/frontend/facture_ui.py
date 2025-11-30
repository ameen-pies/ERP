import streamlit as st
import requests
from datetime import datetime

# Configuration
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Gestion Factures",
    layout="wide",
    page_icon="📄",
    initial_sidebar_state="collapsed"  # Masquer la sidebar
)

# Cacher complètement la sidebar avec CSS
st.markdown("""
<style>
    /* Masquer complètement la sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Ajuster le contenu principal pour prendre toute la largeur */
    .main .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .success-box {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .section-divider {
        height: 3px;
        background: linear-gradient(to right, #667eea, #764ba2);
        margin: 40px 0;
        border-radius: 2px;
    }
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #667eea;
    }
    .section-header {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)


def status_badge(status):
    """Génère un badge de statut coloré"""
    colors = {
        "Validée": ("🟢", "#d1fae5", "#065f46"),
        "En attente correction": ("🟡", "#fef3c7", "#92400e"),
        "Approuvée": ("🟢", "#d1fae5", "#065f46"),
        "Rejetée": ("🔴", "#fee2e2", "#991b1b"),
        "Payée": ("💚", "#d1fae5", "#065f46")
    }
    icon, bg, color = colors.get(status, ("⚪", "#f3f4f6", "#6b7280"))
    return f'<span style="background-color:{bg}; color:{color}; padding:5px 12px; border-radius:12px; font-weight:600;">{icon} {status}</span>'


# ==================== HEADER ====================
st.markdown("""
<div class="main-header">
    <h1 style="margin:0;">📄 Gestion des Factures ERP</h1>
    <p style="margin:10px 0 0 0; opacity:0.9;">Extraction OCR • Validation PO • Suivi des paiements</p>
</div>
""", unsafe_allow_html=True)


# ==================== SECTION 1: LISTE DES FACTURES (HAUT) ====================
st.markdown("""
<div class="section-header">
    <h2 style="margin:0; color:#1f2937;">📋 Liste Complète des Factures</h2>
    <p style="margin:5px 0 0 0; color:#6b7280;">Toutes les factures traitées avec leur statut de validation</p>
</div>
""", unsafe_allow_html=True)

# Filtres et statistiques
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])

with col1:
    filter_status = st.selectbox(
        "📊 Filtrer par statut",
        ["Tous", "Validée", "En attente correction", "Approuvée", "Rejetée", "Payée"]
    )

with col2:
    search_po = st.text_input("🔍 Rechercher PO", placeholder="PO-XXX")

with col3:
    search_facture = st.text_input("🔍 Rechercher Facture", placeholder="FACT-XXX")

with col4:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.rerun()

with col5:
    # Statistiques rapides
    try:
        stats_response = requests.get(f"{API_URL}/factures/stats/summary", timeout=3)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            st.metric("Total", stats['total'])
    except:
        pass

st.markdown("---")

# Liste des factures
try:
    params = {}
    if filter_status != "Tous":
        params["status"] = filter_status
    if search_po:
        params["po_id"] = search_po
    
    response = requests.get(f"{API_URL}/factures/", params=params)
    
    if response.status_code == 200:
        data = response.json()
        factures = data.get("factures", [])
        
        # Filtrer par numéro de facture si recherche
        if search_facture:
            factures = [f for f in factures if search_facture.lower() in f.get('facture_id', '').lower()]
        
        if not factures:
            st.info("🔭 Aucune facture trouvée")
        else:
            st.write(f"**{len(factures)} facture(s) trouvée(s)**")
            
            # Affichage en table compacte
            for idx, facture in enumerate(factures):
                with st.expander(
                    f"📄 {facture['facture_id']} | {facture.get('fournisseur_nom', 'N/A')} | "
                    f"{facture.get('montant_ttc', 0):.2f} {facture.get('devise', 'TND')} | "
                    f"PO: {facture['linked_po_id']}"
                ):
                    # Statut
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(status_badge(facture['status']), unsafe_allow_html=True)
                    with col2:
                        date_reception = datetime.fromisoformat(facture['date_reception']).strftime("%d/%m/%Y %H:%M")
                        st.caption(f"Reçu le: {date_reception}")
                    
                    st.markdown("---")
                    
                    # Détails en 4 colonnes
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write("**📊 Général**")
                        st.write(f"• ID: {facture['facture_id']}")
                        st.write(f"• N° Facture: {facture.get('numero_facture', 'N/A')}")
                        st.write(f"• PO: {facture['linked_po_id']}")
                        st.write(f"• Type: {facture.get('type_achat', 'N/A')}")
                    
                    with col2:
                        st.write("**🏢 Fournisseur**")
                        st.write(f"• Nom: {facture.get('fournisseur_nom', 'N/A')}")
                        st.write(f"• Matricule: {facture.get('fournisseur_matricule', 'N/A')}")
                    
                    with col3:
                        st.write("**💰 Montants**")
                        st.write(f"• HT: {facture.get('montant_ht', 0):.2f} {facture.get('devise', 'TND')}")
                        st.write(f"• TVA: {facture.get('montant_tva', 0):.2f} {facture.get('devise', 'TND')}")
                        st.write(f"• **TTC: {facture.get('montant_ttc', 0):.2f} {facture.get('devise', 'TND')}**")
                    
                    with col4:
                        st.write("**📦 Quantité**")
                        st.write(f"• Qté: {facture.get('quantite', 'N/A')} {facture.get('unite', '')}")
                        st.write(f"• Date facture: {facture.get('date_facture', 'N/A')}")
                    
                    # Résultat validation
                    if facture.get('validation_result'):
                        validation = facture['validation_result']
                        
                        st.markdown("---")
                        st.markdown("**✅ Résultat validation PO**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Score", f"{validation['confidence_score']}%")
                        with col2:
                            status_val = "✅ Valide" if validation['is_valid'] else "❌ Invalide"
                            st.write(status_val)
                        with col3:
                            st.write(f"Champs OK: {len(validation['matched_fields'])}/10")
                        
                        if validation['errors']:
                            with st.expander("❌ Voir les erreurs"):
                                for error in validation['errors']:
                                    st.error(error)
                        
                        if validation['warnings']:
                            with st.expander("⚠️ Voir les avertissements"):
                                for warning in validation['warnings']:
                                    st.warning(warning)
                    
                    # Actions
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if facture['status'] in ["Validée", "En attente correction"]:
                            if st.button(f"✅ Approuver", key=f"approve_{idx}"):
                                resp = requests.post(
                                    f"{API_URL}/factures/{facture['facture_id']}/approve",
                                    data={"user": "comptable"}
                                )
                                if resp.status_code == 200:
                                    st.success("✅ Approuvée!")
                                    st.rerun()
                    
                    with col2:
                        if facture['status'] == "Approuvée":
                            if st.button(f"💰 Marquer payée", key=f"paid_{idx}"):
                                resp = requests.post(
                                    f"{API_URL}/factures/{facture['facture_id']}/mark-paid",
                                    data={"user": "comptable"}
                                )
                                if resp.status_code == 200:
                                    st.success("💰 Payée!")
                                    st.rerun()
                    
                    with col3:
                        if facture['status'] in ["Validée", "En attente correction"]:
                            if st.button(f"❌ Rejeter", key=f"reject_btn_{idx}"):
                                st.session_state[f"show_reject_{idx}"] = True
                    
                    # Formulaire de rejet
                    if st.session_state.get(f"show_reject_{idx}", False):
                        with col4:
                            reason = st.text_input("Raison", key=f"reason_{idx}")
                            if st.button("Confirmer", key=f"confirm_{idx}"):
                                if reason:
                                    resp = requests.post(
                                        f"{API_URL}/factures/{facture['facture_id']}/reject",
                                        data={"user": "comptable", "reason": reason}
                                    )
                                    if resp.status_code == 200:
                                        st.success("❌ Rejetée!")
                                        st.session_state[f"show_reject_{idx}"] = False
                                        st.rerun()
    
    else:
        st.error("❌ Erreur lors de la récupération des factures")

except Exception as e:
    st.error(f"❌ Erreur: {str(e)}")


# ==================== DIVIDER ====================
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# ==================== SECTION 2: UPLOAD NOUVELLE FACTURE (BAS) ====================
st.markdown("""
<div class="section-header">
    <h2 style="margin:0; color:#1f2937;">📤 Upload et Validation d'une Nouvelle Facture</h2>
    <p style="margin:5px 0 0 0; color:#6b7280;">Téléchargez une facture pour extraction OCR automatique et validation contre PO</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>🔄 Processus automatique:</strong><br>
    1️⃣ Upload fichier → 2️⃣ Hébergement temporaire (ImgBB) → 3️⃣ OCR extraction (RapidAPI) → 4️⃣ Comparaison avec PO → 5️⃣ Validation
</div>
""", unsafe_allow_html=True)

with st.form("facture_upload_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        po_id = st.text_input(
            "🔗 Purchase Order ID *",
            placeholder="PO-001",
            help="ID du bon de commande à valider"
        )
    
    with col2:
        user_email = st.text_input(
            "📧 Votre Email *",
            placeholder="votre.email@company.com"
        )
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "📎 Sélectionner la facture (PDF, PNG, JPG) *",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Formats acceptés: PDF, PNG, JPG, JPEG"
    )
    
    if uploaded_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"✅ Fichier: {uploaded_file.name}")
        with col2:
            st.info(f"📦 Taille: {uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.info(f"📄 Type: {uploaded_file.type}")
        
        # Aperçu si image
        if uploaded_file.type in ['image/png', 'image/jpeg', 'image/jpg']:
            with st.expander("👁️ Voir l'aperçu de l'image"):
                st.image(uploaded_file, caption="Aperçu de la facture", use_container_width=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submit = st.form_submit_button(
            "🚀 Traiter & Valider la Facture",
            type="primary",
            use_container_width=True
        )

# Traitement du formulaire
if submit:
    if not po_id or not user_email or not uploaded_file:
        st.error("⚠️ Veuillez remplir tous les champs obligatoires et sélectionner un fichier")
    else:
        with st.spinner("🔄 Traitement en cours... (Upload → OCR → Validation)"):
            # Préparer le fichier
            files = {
                "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }
            
            form_data = {
                "po_id": po_id,
                "user_email": user_email
            }
            
            try:
                # Appel API
                response = requests.post(
                    f"{API_URL}/factures/upload-and-validate",
                    data=form_data,
                    files=files,
                    timeout=60  # 60 secondes timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Animation de succès
                    st.balloons()
                    
                    st.success(f"✅ Facture traitée avec succès: **{result['facture_id']}**")
                    
                    # Afficher les résultats dans des onglets
                    tab1, tab2, tab3 = st.tabs(["📊 Résumé", "🔍 Données OCR", "✅ Validation PO"])
                    
                    # TAB 1: Résumé
                    with tab1:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("📄 Facture ID", result['facture_id'])
                        with col2:
                            st.metric("🔗 PO Lié", result['linked_po_id'])
                        with col3:
                            st.markdown(status_badge(result['status']), unsafe_allow_html=True)
                        with col4:
                            validation = result['validation_results']
                            score = validation['confidence_score']
                            st.metric("🎯 Score", f"{score}%")
                        
                        st.markdown("---")
                        st.info("💡 La facture a été ajoutée à la liste ci-dessus. Actualisez pour la voir.")
                    
                    # TAB 2: OCR
                    with tab2:
                        st.subheader("🔍 Données extraites par OCR")
                        
                        ocr = result['ocr_results']
                        extracted = ocr['extracted_fields']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📄 Informations générales**")
                            st.write(f"• Numéro facture: {extracted.get('numero_facture', 'N/A')}")
                            st.write(f"• Fournisseur: {extracted.get('fournisseur', 'N/A')}")
                            st.write(f"• Date: {extracted.get('date_facture', 'N/A')}")
                            st.write(f"• Type achat: {extracted.get('type_achat', 'N/A')}")
                            
                            st.metric(
                                "Confiance OCR",
                                f"{ocr['confidence']*100:.1f}%",
                                help="Fiabilité de l'extraction"
                            )
                        
                        with col2:
                            st.markdown("**💰 Montants et quantités**")
                            st.write(f"• Montant TTC: **{extracted.get('montant_ttc', 0):.2f} {extracted.get('devise', 'TND')}**")
                            st.write(f"• Quantité: {extracted.get('quantite', 'N/A')}")
                            st.write(f"• Devise: {extracted.get('devise', 'TND')}")
                    
                    # TAB 3: Validation
                    with tab3:
                        st.subheader("✅ Validation contre Purchase Order")
                        
                        validation = result['validation_results']
                        
                        # Statut global
                        if validation['is_valid']:
                            st.markdown("""
                            <div class="success-box">
                                <h3 style="margin:0; color:#065f46;">✅ Validation Réussie</h3>
                                <p style="margin:5px 0 0 0;">La facture correspond au bon de commande</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="error-box">
                                <h3 style="margin:0; color:#991b1b;">❌ Validation Échouée</h3>
                                <p style="margin:5px 0 0 0;">Des différences ont été détectées</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Champs validés
                        if validation['matched_fields']:
                            st.markdown("**✅ Champs validés:**")
                            cols = st.columns(min(len(validation['matched_fields']), 5))
                            for idx, field in enumerate(validation['matched_fields']):
                                with cols[idx % 5]:
                                    st.success(f"✓ {field}")
                        
                        # Erreurs
                        if validation['errors']:
                            st.markdown("---")
                            st.markdown("**❌ Erreurs critiques:**")
                            for error in validation['errors']:
                                st.error(error)
                        
                        # Avertissements
                        if validation['warnings']:
                            st.markdown("---")
                            st.markdown("**⚠️ Avertissements:**")
                            for warning in validation['warnings']:
                                st.warning(warning)
                        
                        # Comparaison détaillée
                        if validation['mismatches']:
                            st.markdown("---")
                            st.markdown("**📊 Comparaison détaillée:**")
                            for mismatch in validation['mismatches']:
                                severity = mismatch['severity']
                                box_class = "error-box" if severity == "error" else "warning-box"
                                icon = "❌" if severity == "error" else "⚠️"
                                
                                st.markdown(f"""
                                <div class="{box_class}">
                                    <strong>{icon} {mismatch['field']}</strong><br>
                                    <table style="width:100%; margin-top:10px;">
                                        <tr>
                                            <td style="width:150px;"><strong>PO:</strong></td>
                                            <td>{mismatch['po_value']}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Facture:</strong></td>
                                            <td>{mismatch['facture_value']}</td>
                                        </tr>
                                        {f"<tr><td><strong>Différence:</strong></td><td>{mismatch.get('difference', '')}</td></tr>" if 'difference' in mismatch else ""}
                                    </table>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if not validation['errors'] and not validation['warnings']:
                            st.success("🎉 Aucun problème détecté! La facture peut être approuvée.")
                    
                    # Bouton pour actualiser la page
                    if st.button("🔄 Actualiser la liste des factures"):
                        st.rerun()
                
                else:
                    st.error(f"❌ Erreur API: {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.error(f"Détails: {error_detail.get('detail', response.text)}")
                    except:
                        st.error(response.text)
            
            except requests.exceptions.Timeout:
                st.error("⏱️ Le traitement a pris trop de temps. Veuillez réessayer.")
            except Exception as e:
                st.error(f"❌ Erreur de connexion: {str(e)}")


# Footer
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 20px;">
    <p><strong>📄 Gestion Factures ERP v1.0</strong></p>
    <p>Extraction OCR automatique • Validation PO • Suivi des paiements</p>
</div>
""", unsafe_allow_html=True)