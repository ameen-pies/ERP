import streamlit as st
import requests
from datetime import datetime

# Configuration
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Gestion Factures",
    layout="wide",
    page_icon="📄",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Ajuster le contenu principal */
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
        color: #065f46;
    }
    .success-box h3 {
        color: #065f46 !important;
        margin: 0;
    }
    .success-box p {
        color: #047857 !important;
        margin: 5px 0 0 0;
    }
    .error-box {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #991b1b;
    }
    .error-box h3 {
        color: #991b1b !important;
        margin: 0;
    }
    .error-box p {
        color: #b91c1c !important;
        margin: 5px 0 0 0;
    }
    .error-box strong {
        color: #7f1d1d !important;
    }
    .warning-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #92400e;
    }
    .warning-box strong {
        color: #78350f !important;
    }
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #1e3a8a;
    }
    .info-box strong {
        color: #1e40af !important;
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
    .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        background-color: white;
    }
    .comparison-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #e5e7eb;
    }
    .comparison-table td:first-child {
        font-weight: 600;
        width: 150px;
        color: #374151;
    }
    .comparison-table td:last-child {
        color: #1f2937;
    }
    
    /* Progress indicator styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(to right, #667eea, #764ba2);
    }
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
st.sidebar.title("🏢 ERP Achat")
st.sidebar.markdown("### 📄 Module Factures")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["📋 Liste des Factures", "📤 Upload Nouvelle Facture", "📊 Statistiques"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**ERP Factures v1.0**")
st.sidebar.markdown("OCR • Validation • Paiement")


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


def safe_format_amount(value, default="N/A"):
    """Safely format amount, handling None values"""
    if value is None:
        return default
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return default


# ==================== HEADER ====================
st.markdown("""
<div class="main-header">
    <h1 style="margin:0;">📄 Gestion des Factures ERP</h1>
    <p style="margin:10px 0 0 0; opacity:0.9;">Extraction OCR • Validation PO • Suivi des paiements</p>
</div>
""", unsafe_allow_html=True)


# ==================== PAGE: LISTE DES FACTURES ====================
if page == "📋 Liste des Factures":
    st.markdown("""
    <div class="section-header">
        <h2 style="margin:0; color:#1f2937;">📋 Liste Complète des Factures</h2>
        <p style="margin:5px 0 0 0; color:#6b7280;">Toutes les factures traitées avec leur statut de validation</p>
    </div>
    """, unsafe_allow_html=True)

    # Filtres et statistiques
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        filter_status = st.selectbox(
            "📊 Filtrer par statut",
            ["Tous", "Validée", "En attente correction", "Approuvée", "Rejetée", "Payée"]
        )

    with col2:
        search_po = st.text_input("🔍 Rechercher PO", placeholder="BC-XXX")

    with col3:
        search_facture = st.text_input("🔍 Rechercher Facture", placeholder="FACT-XXX")

    with col4:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Liste des factures
    try:
        params = {}
        if filter_status != "Tous":
            params["status"] = filter_status
        if search_po:
            params["po_id"] = search_po
        
        response = requests.get(f"{API_URL}/factures/", params=params, timeout=30)
        
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
                    # Safe formatting for display
                    montant_ttc = facture.get('montant_ttc')
                    montant_display = safe_format_amount(montant_ttc)
                    devise = facture.get('devise', 'TND')
                    
                    with st.expander(
                        f"📄 {facture['facture_id']} | {facture.get('fournisseur_nom', 'N/A')} | "
                        f"{montant_display} {devise} | "
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
                            montant_ht = safe_format_amount(facture.get('montant_ht'))
                            montant_tva = safe_format_amount(facture.get('montant_tva'))
                            
                            st.write(f"• HT: {montant_ht} {devise}")
                            st.write(f"• TVA: {montant_tva} {devise}")
                            st.write(f"• **TTC: {montant_display} {devise}**")
                        
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
                                st.markdown("**❌ Erreurs:**")
                                for error in validation['errors']:
                                    st.error(error)
                            
                            if validation['warnings']:
                                st.markdown("**⚠️ Avertissements:**")
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
                                        data={"user": "comptable"},
                                        timeout=30
                                    )
                                    if resp.status_code == 200:
                                        st.success("✅ Approuvée!")
                                        st.rerun()
                        
                        with col2:
                            if facture['status'] == "Approuvée":
                                if st.button(f"💰 Marquer payée", key=f"paid_{idx}"):
                                    resp = requests.post(
                                        f"{API_URL}/factures/{facture['facture_id']}/mark-paid",
                                        data={"user": "comptable"},
                                        timeout=30
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
                                            data={"user": "comptable", "reason": reason},
                                            timeout=30
                                        )
                                        if resp.status_code == 200:
                                            st.success("❌ Rejetée!")
                                            st.session_state[f"show_reject_{idx}"] = False
                                            st.rerun()
        
        else:
            st.error("❌ Erreur lors de la récupération des factures")

    except requests.exceptions.Timeout:
        st.error("⏱️ La requête a pris trop de temps. Veuillez réessayer.")
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")


# ==================== PAGE: UPLOAD NOUVELLE FACTURE ====================
elif page == "📤 Upload Nouvelle Facture":
    st.markdown("""
    <div class="section-header">
        <h2 style="margin:0; color:#1f2937;">📤 Upload et Validation d'une Nouvelle Facture</h2>
        <p style="margin:5px 0 0 0; color:#6b7280;">Téléchargez une facture pour extraction OCR automatique et validation contre PO</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>📄 Processus automatique:</strong><br>
        <span style="color: #1e40af;">1️⃣ Upload fichier → 2️⃣ OCR extraction (EasyOCR) → 3️⃣ Comparaison avec PO → 4️⃣ Validation</span><br>
        <span style="color: #1e40af;">⏱️ <strong>Temps estimé:</strong> 30-90 secondes pour PDF multi-pages, 10-30 secondes pour images</span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("facture_upload_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            po_id = st.text_input(
                "🔗 Purchase Order ID *",
                placeholder="BC-001",
                help="ID du bon de commande à valider"
            )
        
        with col2:
            user_email = st.text_input(
                "📧 Votre Email *",
                placeholder="votre.email@company.com"
            )
        
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "🖼️ Sélectionner la facture (PDF, PNG, JPG) *",
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
                file_type = uploaded_file.type
                st.info(f"📄 Type: {file_type}")
                
                # Estimate processing time
                if 'pdf' in file_type.lower():
                    st.warning("⏱️ PDF: ~30-90 sec")
                else:
                    st.info("⏱️ Image: ~10-30 sec")
            
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
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Timer display
            import time
            start_time = time.time()
            timer_placeholder = st.empty()
            
            try:
                status_text.info("📤 Préparation du fichier...")
                progress_bar.progress(10)
                
                # Préparer le fichier
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                
                form_data = {
                    "po_id": po_id,
                    "user_email": user_email
                }
                
                status_text.info("🔄 Envoi au serveur et traitement OCR en cours...")
                progress_bar.progress(20)
                
                # Start a timer thread to show elapsed time
                processing = True
                def update_timer():
                    while processing:
                        elapsed = time.time() - start_time
                        timer_placeholder.info(f"⏱️ Temps écoulé: {elapsed:.1f}s")
                        time.sleep(0.5)
                
                import threading
                timer_thread = threading.Thread(target=update_timer, daemon=True)
                timer_thread.start()
                
                # Appel API avec timeout augmenté
                response = requests.post(
                    f"{API_URL}/factures/upload-and-validate",
                    data=form_data,
                    files=files,
                    timeout=300  # ✅ INCREASED TO 5 MINUTES (300 seconds)
                )
                
                processing = False
                progress_bar.progress(100)
                
                elapsed_time = time.time() - start_time
                timer_placeholder.success(f"✅ Traitement terminé en {elapsed_time:.1f} secondes")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Animation de succès
                    st.balloons()
                    
                    status_text.success(f"✅ Facture traitée avec succès: **{result['facture_id']}**")
                    
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
                        st.info("💡 La facture a été ajoutée. Consultez l'onglet 'Liste des Factures' pour la voir.")
                    
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
                            montant_ttc_ocr = safe_format_amount(extracted.get('montant_ttc'))
                            st.write(f"• Montant TTC: **{montant_ttc_ocr} {extracted.get('devise', 'TND')}**")
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
                                <h3>✅ Validation Réussie</h3>
                                <p>La facture correspond au bon de commande</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="error-box">
                                <h3>❌ Validation Échouée</h3>
                                <p>Des différences ont été détectées</p>
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
                                    <table class="comparison-table">
                                        <tr>
                                            <td>PO:</td>
                                            <td>{mismatch['po_value']}</td>
                                        </tr>
                                        <tr>
                                            <td>Facture:</td>
                                            <td>{mismatch['facture_value']}</td>
                                        </tr>
                                        {f"<tr><td>Différence:</td><td>{mismatch.get('difference', '')}</td></tr>" if 'difference' in mismatch else ""}
                                    </table>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if not validation['errors'] and not validation['warnings']:
                            st.success("🎉 Aucun problème détecté! La facture peut être approuvée.")
                
                else:
                    processing = False
                    status_text.error(f"❌ Erreur API: {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.error(f"Détails: {error_detail.get('detail', response.text)}")
                    except:
                        st.error(response.text)
            
            except requests.exceptions.Timeout:
                processing = False
                status_text.error("⏱️ Le traitement a pris trop de temps (> 5 minutes). Le fichier est peut-être trop volumineux ou complexe.")
                st.error("💡 Suggestions: Essayez avec une image de meilleure qualité ou un PDF avec moins de pages.")
            except Exception as e:
                processing = False
                status_text.error(f"❌ Erreur de connexion: {str(e)}")


# ==================== PAGE: STATISTIQUES ====================
elif page == "📊 Statistiques":
    st.markdown("""
    <div class="section-header">
        <h2 style="margin:0; color:#1f2937;">📊 Statistiques des Factures</h2>
        <p style="margin:5px 0 0 0; color:#6b7280;">Vue d'ensemble et analyse des factures traitées</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        stats_response = requests.get(f"{API_URL}/factures/stats/summary", timeout=30)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Total Factures", stats['total'])
            with col2:
                st.metric("💰 Montant Total", f"{stats['total_amount']:.2f} TND")
            with col3:
                st.metric("🎯 Confiance OCR Moy.", f"{stats['average_confidence']*100:.1f}%")
            with col4:
                validees = stats['by_status'].get('Validée', 0)
                pct = (validees / stats['total'] * 100) if stats['total'] > 0 else 0
                st.metric("✅ Taux Validation", f"{pct:.1f}%")
            
            st.markdown("---")
            
            # Répartition par statut
            st.subheader("📊 Répartition par Statut")
            
            status_cols = st.columns(len(stats['by_status']))
            for idx, (status, count) in enumerate(stats['by_status'].items()):
                with status_cols[idx]:
                    st.markdown(status_badge(status), unsafe_allow_html=True)
                    st.metric("", count)
            
            st.markdown("---")
            
            # Factures récentes
            st.subheader("🕐 Factures Récentes")
            response = requests.get(f"{API_URL}/factures/", timeout=30)
            if response.status_code == 200:
                factures = response.json().get('factures', [])
                recent = sorted(factures, key=lambda x: x['date_reception'], reverse=True)[:5]
                
                for facture in recent:
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                    with col1:
                        st.write(f"**{facture['facture_id']}**")
                    with col2:
                        st.write(facture.get('fournisseur_nom', 'N/A'))
                    with col3:
                        st.markdown(status_badge(facture['status']), unsafe_allow_html=True)
                    with col4:
                        montant = safe_format_amount(facture.get('montant_ttc'))
                        st.write(f"{montant} {facture.get('devise', 'TND')}")
        else:
            st.error("❌ Erreur lors de la récupération des statistiques")
    
    except requests.exceptions.Timeout:
        st.error("⏱️ La requête a pris trop de temps. Veuillez réessayer.")
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")


# Footer
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 20px;">
    <p><strong>📄 Gestion Factures ERP v1.0</strong></p>
    <p>Extraction OCR automatique • Validation PO • Suivi des paiements</p>
</div>
""", unsafe_allow_html=True)