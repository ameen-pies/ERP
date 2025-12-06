import json

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api"


def fetch_json(endpoint: str, params: dict | None = None):
    try:
        response = requests.get(
            f"{API_BASE_URL}/{endpoint}", params=params, timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return []


def post_json(endpoint: str, payload: dict):
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Submission error: {exc}")
        return None


def set_page_defaults():
    st.set_page_config(
        page_title="Mini ERP - GRN",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Custom CSS for prettier UI
    st.markdown("""
        <style>
        /* Main styling */
        .main {
            padding: 2rem 1rem;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
            color: white;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Radio button styling */
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            color: white;
            font-weight: 500;
            padding: 0.5rem;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: rgba(255,255,255,0.1);
        }
        
        /* Header styling */
        h1 {
            color: #667eea;
            font-weight: 700;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        h2 {
            color: #764ba2;
            font-weight: 600;
            margin-top: 1.5rem;
        }
        
        h3 {
            color: #667eea;
            font-weight: 600;
        }
        
        /* Metric cards */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
        }
        
        /* Button styling */
        button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Success/Info/Warning boxes */
        [data-testid="stSuccess"] {
            border-left: 4px solid #28a745;
            border-radius: 8px;
            padding: 1rem;
        }
        
        [data-testid="stInfo"] {
            border-left: 4px solid #17a2b8;
            border-radius: 8px;
            padding: 1rem;
        }
        
        [data-testid="stWarning"] {
            border-left: 4px solid #ffc107;
            border-radius: 8px;
            padding: 1rem;
        }
        
        [data-testid="stError"] {
            border-left: 4px solid #dc3545;
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Dataframe styling */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Expander styling */
        [data-testid="stExpander"] {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        
        /* Tabs styling */
        [data-testid="stTabs"] {
            margin-top: 1rem;
        }
        
        [data-testid="stTab"] {
            border-radius: 8px 8px 0 0;
        }
        
        /* Input styling */
        input, select, textarea {
            border-radius: 6px;
        }
        
        /* Divider styling */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #e0e0e0;
        }
        
        /* Card-like containers */
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("📦 Mini ERP")
    st.sidebar.markdown("---")


def show_dashboard():
    st.markdown("## 📊 ERP Dashboard")
    st.markdown("### Overview of Purchase Orders, Suppliers, and Goods Receipt Notes")
    st.markdown("---")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📋 Purchase Orders", "🏢 Suppliers", "📦 Goods Receipt Notes"])
    
    # ========== PURCHASE ORDERS TAB ==========
    with tab1:
        st.subheader("Purchase Orders")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            po_search = st.text_input(
                "Search POs",
                placeholder="Search by PO number, supplier, or item",
                key="dashboard_po_search"
            )
        with col2:
            po_status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Pending", "Closed"],
                key="dashboard_po_status"
            )
        
        # Fetch POs with filters
        params = {}
        if po_search:
            params["search"] = po_search
        if po_status_filter != "All":
            params["status"] = po_status_filter.lower()
        
        pos = fetch_json("po", params=params if params else None)
        
        if pos:
            # Summary statistics
            total_pos = len(pos)
            pending_count = sum(1 for po in pos if po.get("status") == "pending")
            closed_count = sum(1 for po in pos if po.get("status") == "closed")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total POs", total_pos)
            with col2:
                st.metric("Pending", pending_count)
            with col3:
                st.metric("Closed", closed_count)
            
            st.divider()
            
            # PO List
            po_data = []
            for po in pos:
                total_lines = len(po.get("lines", []))
                closed_lines = sum(1 for line in po.get("lines", []) if line.get("status") == "closed")
                po_data.append({
                    "PO Number": po.get("po_number", "N/A"),
                    "Supplier": po.get("supplier", "N/A"),
                    "Status": po.get("status", "unknown").upper(),
                    "Lines": f"{closed_lines}/{total_lines}",
                    "Created": po.get("created_at", "N/A")[:10] if po.get("created_at") else "N/A",
                })
            
            st.dataframe(po_data, use_container_width=True, hide_index=True)
            
            # Detailed view
            st.subheader("PO Details")
            selected_po = st.selectbox(
                "Select PO to view details",
                options=[f"{po['po_number']} - {po['supplier']}" for po in pos],
                key="dashboard_po_select"
            )
            if selected_po:
                selected_po_data = next(
                    (po for po in pos if f"{po['po_number']} - {po['supplier']}" == selected_po),
                    None
                )
                if selected_po_data:
                    with st.expander("View PO Details", expanded=True):
                        st.write(f"**PO Number:** {selected_po_data.get('po_number')}")
                        st.write(f"**Supplier:** {selected_po_data.get('supplier')}")
                        st.write(f"**Status:** {selected_po_data.get('status', 'unknown')}")
                        st.write(f"**Created:** {selected_po_data.get('created_at', 'N/A')}")
                        
                        st.write("**PO Lines:**")
                        lines_data = []
                        for line in selected_po_data.get("lines", []):
                            remaining = line.get("qty_ordered", 0) - line.get("qty_received", 0)
                            lines_data.append({
                                "Item": line.get("item_name", "N/A"),
                                "Ordered": line.get("qty_ordered", 0),
                                "Received": line.get("qty_received", 0),
                                "Remaining": max(remaining, 0),
                                "Status": line.get("status", "open").upper(),
                            })
                        if lines_data:
                            st.dataframe(lines_data, use_container_width=True, hide_index=True)
        else:
            st.info("No purchase orders found.")
    
    # ========== SUPPLIERS TAB ==========
    with tab2:
        st.subheader("Suppliers")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            supplier_search = st.text_input(
                "Search Suppliers",
                placeholder="Search by name or ID",
                key="dashboard_supplier_search"
            )
        with col2:
            supplier_status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Active", "Inactive"],
                key="dashboard_supplier_status"
            )
        
        # Fetch suppliers
        params = {}
        if supplier_search:
            params["search"] = supplier_search
        
        suppliers = fetch_json("suppliers", params=params if params else None)
        
        # Filter by status if needed
        if supplier_status_filter != "All":
            status_value = "ACTIVE" if supplier_status_filter == "Active" else None
            suppliers = [s for s in suppliers if s.get("status") == status_value]
        
        if suppliers:
            # Summary statistics
            total_suppliers = len(suppliers)
            active_count = sum(1 for s in suppliers if s.get("status") == "ACTIVE")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Suppliers", total_suppliers)
            with col2:
                st.metric("Active Suppliers", active_count)
            
            st.divider()
            
            # Supplier List
            supplier_data = []
            for supplier in suppliers:
                supplier_data.append({
                    "Name": supplier.get("name", "N/A"),
                    "ID": supplier.get("id", "N/A"),
                    "Category": supplier.get("category", "N/A"),
                    "Status": supplier.get("status", "N/A"),
                    "Email": supplier.get("email", "N/A"),
                    "Phone": supplier.get("phone", "N/A"),
                })
            
            st.dataframe(supplier_data, use_container_width=True, hide_index=True)
            
            # Detailed view
            st.subheader("Supplier Details")
            selected_supplier = st.selectbox(
                "Select Supplier to view details",
                options=[f"{s['name']} ({s.get('id', 'N/A')})" for s in suppliers],
                key="dashboard_supplier_select"
            )
            if selected_supplier:
                selected_supplier_data = next(
                    (s for s in suppliers if f"{s['name']} ({s.get('id', 'N/A')})" == selected_supplier),
                    None
                )
                if selected_supplier_data:
                    with st.expander("View Supplier Details", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Name:** {selected_supplier_data.get('name')}")
                            st.write(f"**ID:** {selected_supplier_data.get('id')}")
                            st.write(f"**Category:** {selected_supplier_data.get('category', 'N/A')}")
                            st.write(f"**Status:** {selected_supplier_data.get('status', 'N/A')}")
                        with col2:
                            st.write(f"**Email:** {selected_supplier_data.get('email', 'N/A')}")
                            st.write(f"**Phone:** {selected_supplier_data.get('phone', 'N/A')}")
                            st.write(f"**Tax ID:** {selected_supplier_data.get('tax_id', 'N/A')}")
                            st.write(f"**Created:** {selected_supplier_data.get('created_at', 'N/A')}")
        else:
            st.info("No suppliers found.")
    
    # ========== GRNs TAB ==========
    with tab3:
        st.subheader("Goods Receipt Notes")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            grn_search = st.text_input(
                "Search GRNs",
                placeholder="Search by GRN reference, PO, or item",
                key="dashboard_grn_search"
            )
        with col2:
            grn_status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Registered", "Pending"],
                key="dashboard_grn_status"
            )
        
        # Fetch GRNs with filters
        params = {}
        if grn_search:
            params["search"] = grn_search
        
        try:
            grns = fetch_json("grn", params=params if params else None)
            if grns is None:
                grns = []
        except Exception as e:
            st.error(f"Error loading GRNs: {e}")
            grns = []
        
        # Filter by status if needed
        if grn_status_filter != "All":
            status_value = "registered" if grn_status_filter == "Registered" else "pending"
            grns = [g for g in grns if g.get("status") == status_value]
        
        if grns:
            # Summary statistics
            total_grns = len(grns)
            registered_count = sum(1 for g in grns if g.get("status") == "registered")
            pending_count = sum(1 for g in grns if g.get("status") == "pending")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total GRNs", total_grns)
            with col2:
                st.metric("Registered", registered_count)
            with col3:
                st.metric("Pending", pending_count)
            
            st.divider()
            
            # GRN List - Use stored PO reference directly for optimal performance
            grn_data = []
            for grn in grns:
                # Use stored po_reference directly (no API calls needed)
                po_number = grn.get("po_reference", "N/A")
                
                total_lines = len(grn.get("lines", []))
                passed_lines = sum(1 for line in grn.get("lines", []) if line.get("quality_status") == "pass")
                grn_data.append({
                    "GRN Reference": grn.get("reference", "N/A"),
                    "PO Reference": po_number,
                    "Status": grn.get("status", "unknown").upper(),
                    "Lines": f"{passed_lines}/{total_lines}",
                    "Created": grn.get("created_at", "N/A")[:10] if grn.get("created_at") else "N/A",
                })
            
            st.dataframe(grn_data, use_container_width=True, hide_index=True)
            
            # Detailed view
            st.subheader("GRN Details")
            selected_grn = st.selectbox(
                "Select GRN to view details",
                options=[f"{g['reference']} - {g.get('status', 'unknown')}" for g in grns],
                key="dashboard_grn_select"
            )
            if selected_grn:
                selected_grn_data = next(
                    (g for g in grns if f"{g['reference']} - {g.get('status', 'unknown')}" == selected_grn),
                    None
                )
                if selected_grn_data:
                    # Use stored po_reference directly (no API call needed)
                    po_number = selected_grn_data.get('po_reference', 'N/A')
                    
                    with st.expander("View GRN Details", expanded=True):
                        st.write(f"**GRN Reference:** {selected_grn_data.get('reference')}")
                        st.write(f"**PO Reference:** {po_number}")
                        st.write(f"**Status:** {selected_grn_data.get('status', 'unknown').upper()}")
                        st.write(f"**Created:** {selected_grn_data.get('created_at', 'N/A')}")
                        
                        st.write("**GRN Lines:**")
                        lines_data = []
                        for line in selected_grn_data.get("lines", []):
                            # Use total_received for accurate remaining calculation
                            total_received = line.get("total_received", line.get("current_received", 0))
                            qty_ordered = line.get("qty_ordered", 0)
                            # Calculate remaining based on total received, not just accepted
                            remaining = max(qty_ordered - total_received, 0)
                            
                            lines_data.append({
                                "Item": line.get("item_name", "N/A"),
                                "Ordered": qty_ordered,
                                "Received": line.get("received_qty", 0),  # Received in this GRN
                                "Accepted": line.get("accepted_qty", 0),
                                "Quality": line.get("quality_status", "N/A").upper(),
                                "Remaining": remaining,  # Correct remaining based on total received
                            })
                        if lines_data:
                            st.dataframe(lines_data, use_container_width=True, hide_index=True)
        else:
            st.info("No GRNs found.")


def show_po_creator():
    st.markdown("## 📝 Create Purchase Order")
    st.markdown("### Enter supplier and lines below. Default placeholders help you test quickly.")
    st.markdown("---")

    po_search = st.text_input(
        "Search Purchase Orders",
        placeholder="PO number, supplier, or item",
        key="po-search",
    )
    search_params = {"search": po_search} if po_search else None
    existing_pos = fetch_json("po", params=search_params)
    with st.expander("Existing Purchase Orders"):
        if existing_pos:
            st.table(
                [
                    {
                        "PO": po["po_number"],
                        "Supplier": po["supplier"],
                        "Status": po["status"],
                    }
                    for po in existing_pos
                ]
            )
        else:
            st.write("No purchase orders yet.")

    if "po_line_count" not in st.session_state:
        st.session_state["po_line_count"] = 2

    line_count = st.number_input(
        "PO Line count",
        min_value=1,
        max_value=10,
        value=st.session_state["po_line_count"],
        step=1,
        key="po_line_count_selector",
    )
    st.session_state["po_line_count"] = line_count

    # Load suppliers from database (only product suppliers) - outside form to avoid re-rendering
    suppliers_data = fetch_json("suppliers", params={"products_only": True})
    if not suppliers_data:
        st.warning("No product suppliers found in database. Please add suppliers first.")
        st.stop()
    
    supplier_options = {f"{s.get('name', 'Unknown')} ({s.get('id', 'N/A')})": s.get('name') for s in suppliers_data}
    
    with st.form("po-form"):
        supplier_display = st.selectbox(
            "Select Supplier",
            options=list(supplier_options.keys()),
            key="po_supplier_select"
        )
        supplier = supplier_options[supplier_display] if supplier_display else None
        
        if not supplier:
            st.error("Please select a supplier.")
            st.stop()
        lines_payload = []
        for idx in range(line_count):
            st.markdown(f"**Line {idx + 1}**")
            col1, col2, col3 = st.columns(3)
            item_name = col1.text_input(
                "Item description",
                value="Test Item" if idx == 0 else f"Demo Item {idx + 1}",
                placeholder="Test Item",
                key=f"po_item_{idx}",
            )
            qty = col2.number_input(
                "Quantity ordered",
                min_value=1,
                value=10,
                key=f"po_qty_{idx}",
                help="How many units you requested.",
                step=1,
            )
            price = col3.number_input(
                "Unit price",
                min_value=0.01,
                value=5.0,
                key=f"po_price_{idx}",
                step=0.5,
            )
            lines_payload.append(
                {
                    "item_name": item_name,
                    "qty_ordered": qty,
                    "unit_price": price,
                }
            )

        submitted = st.form_submit_button("Submit PO")
        if submitted:
            payload = {"supplier": supplier, "lines": lines_payload}
            result = post_json("po", payload)
            if result:
                st.success(f"PO {result.get('po_number')} created.")
                st.json(result)

    with st.expander("Search PO lines"):
        line_search = st.text_input(
            "Search by item or supplier", key="po-line-search"
        )
        line_params = {"search": line_search} if line_search else None
        po_lines = fetch_json("po-lines", params=line_params)
        if po_lines:
            st.table(
                [
                    {
                        "PO": line["po_number"],
                        "Supplier": line["supplier"],
                        "Item": line["item_name"],
                        "Ordered": line["qty_ordered"],
                        "Received": line["qty_received"],
                    }
                    for line in po_lines
                ]
            )
        else:
            st.write("No PO lines match your search.")


def show_grn_creator():
    st.markdown("## 📦 Create Goods Receipt Note (GRN)")
    st.markdown("### Select the PO you are receiving against, add received quantities, and record quality.")
    st.markdown("---")

    grn_search = st.text_input(
        "Search GRNs (reference, item, status)", key="grn-search"
    )
    grn_params = {"search": grn_search} if grn_search else None
    grn_records = fetch_json("grn", params=grn_params)
    # Only fetch pending POs with remaining quantities for GRN creation
    pos = fetch_json("po", params={"status": "pending", "has_remaining": True})

    with st.expander("Recent GRNs"):
        if grn_records:
            st.table(
                [
                    {
                        "Reference": grn["reference"],
                        "Status": grn["status"],
                        "Lines": len(grn.get("lines", [])),
                        "Created": grn.get("created_at", "-"),
                    }
                    for grn in grn_records
                ]
            )
        else:
            st.write("No GRNs yet.")
    if not pos:
        st.info("Create a purchase order first.")
        return

    # Show PO reference for easier search
    po_lookup = {f"{po['po_number']} - {po['supplier']}": po for po in pos}
    selected_label = st.selectbox(
        "Select Purchase Order (PO Reference - Supplier)", 
        list(po_lookup.keys()),
        help="Search by PO reference number (e.g., BC-0015)"
    )
    selected_po = po_lookup[selected_label]
    
    # Display selected PO reference prominently
    if selected_po:
        st.info(f"📋 Selected PO: **{selected_po.get('po_number', 'N/A')}** - {selected_po.get('supplier', 'N/A')}")

    if selected_po:
        st.subheader("PO lines")
        lines_table = []
        for line in selected_po["lines"]:
            remaining = max(
                line["qty_ordered"] - line["qty_received"], 0
            )
            lines_table.append(
                {
                    "Item": line["item_name"],
                    "Ordered": line["qty_ordered"],
                    "Remaining": remaining,
                    "Line ID": line["line_id"],
                }
            )
        st.table(lines_table)

        with st.form("grn-form"):
            grn_lines = []
            for idx, line in enumerate(selected_po["lines"]):
                item_name = line.get("item_name", f"Item {idx + 1}")
                qty_ordered = float(line.get("qty_ordered", 0))
                qty_received = float(line.get("qty_received", 0))
                remaining = max(qty_ordered - qty_received, 0)
                
                # Show item name as a header
                st.markdown(f"**{item_name}** (Ordered: {int(qty_ordered)}, Remaining: {int(remaining)})")
                
                col1, col2, col3 = st.columns(3)
                qty = col1.number_input(
                    "Received qty",
                    min_value=0,
                    value=int(remaining),
                    key=f"grn_qty_{idx}",
                    step=1,
                    label_visibility="visible",
                )
                quality = col2.selectbox(
                    "Quality status",
                    options=["pass", "fail"],
                    index=0,
                    key=f"grn_quality_{idx}",
                    label_visibility="visible",
                )
                comments = col3.text_input(
                    "Comments (optional)",
                    placeholder="Add inspection notes",
                    key=f"grn_comments_{idx}",
                    label_visibility="visible",
                )
                st.markdown("---")  # Add separator between items
                grn_lines.append(
                    {
                        "po_line_id": line["line_id"],
                        "received_qty": qty,
                        "quality_status": quality,
                        "comments": comments,
                    }
                )

            triggered = st.form_submit_button("Submit GRN")
            if triggered:
                payload = {"po_id": selected_po["_id"], "lines": grn_lines}
                response = post_json("grn", payload)
                if response:
                    grn_data = response["grn"]
                    grn_status = grn_data.get("status", "registered")
                    
                    if grn_status == "pending":
                        st.warning(f"⚠️ GRN {grn_data.get('reference')} created with PENDING status (quantity mismatch detected)")
                    else:
                        st.success(f"✅ GRN {grn_data.get('reference')} created successfully")
                    
                    # Show updated PO remaining quantities (only if quality passed)
                    po_data = response.get("po", {})
                    st.subheader("Updated PO Status")
                    st.write(f"**PO Number:** {po_data.get('po_number', 'N/A')}")
                    st.write(f"**PO Status:** {po_data.get('status', 'N/A')}")
                    
                    # Show remaining quantities - use GRN lines and anomalies for accurate totals
                    st.subheader("Remaining Quantities")
                    remaining_data = []
                    grn_lines_data = grn_data.get("lines", [])
                    anomalies = response.get("anomalies", [])
                    
                    # Create lookups
                    grn_line_lookup = {line.get("po_line_id"): line for line in grn_lines_data}
                    # Create anomaly lookup by line_id for over-deliveries
                    over_delivery_lookup = {}
                    for anomaly in anomalies:
                        if anomaly.get("issue_type") == "Over-delivery":
                            line_id = anomaly.get("line_id")
                            # Extract total_received from anomaly details or use stored values
                            total_received = anomaly.get("total_received")
                            if not total_received:
                                # Try to parse from details string or use current_received + qty_received
                                current_received = anomaly.get("current_received", 0)
                                qty_received = anomaly.get("qty_received", 0)
                                total_received = current_received + qty_received
                            over_delivery_lookup[line_id] = {
                                "total_received": total_received,
                                "qty_ordered": anomaly.get("qty_ordered", 0)
                            }
                    
                    for po_line in po_data.get("lines", []):
                        po_line_id = po_line.get("line_id")
                        grn_line = grn_line_lookup.get(po_line_id)
                        over_delivery = over_delivery_lookup.get(po_line_id)
                        
                        # Determine total_received and remaining
                        if over_delivery:
                            # For over-delivered items, use anomaly data
                            total_received = over_delivery.get("total_received", po_line.get("qty_received", 0))
                            qty_ordered = over_delivery.get("qty_ordered", po_line.get("qty_ordered", 0))
                            remaining = 0  # Over-delivered items have 0 remaining
                        elif grn_line:
                            # Use GRN line data (has accurate total_received and remaining_qty)
                            total_received = grn_line.get("total_received", po_line.get("qty_received", 0))
                            remaining = grn_line.get("remaining_qty", 0)
                        else:
                            # Fallback to PO line data
                            total_received = po_line.get("qty_received", 0)
                            remaining = max(po_line.get("qty_ordered", 0) - total_received, 0)
                        
                        remaining_data.append({
                            "Item": po_line.get("item_name", "Unknown"),
                            "Ordered": po_line.get("qty_ordered", 0),
                            "Received": total_received,
                            "Remaining": remaining,
                            "Status": po_line.get("status", "open"),
                        })
                    if remaining_data:
                        st.dataframe(remaining_data, use_container_width=True)

                    if response.get("anomalies"):
                        st.warning("⚠️ Anomalies detected (disputes created):")
                        for anomaly in response["anomalies"]:
                            st.write(
                                f"- **{anomaly['issue_type']}** (Line: {anomaly['line_id']}): "
                                f"{anomaly['message']}"
                            )


def show_stock_ledger():
    st.markdown("## 📊 Stock Ledger")
    st.markdown("### Only PASS quality receipts are recorded in stock.")
    st.markdown("---")
    
    # Search functionality
    search_term = st.text_input(
        "Search stock ledger",
        placeholder="Search by item name, GRN reference, or movement type",
        key="stock_search"
    )
    
    # Toggle between list view and grouped by GRN
    view_mode = st.radio(
        "View mode",
        ["Grouped by GRN", "List View"],
        horizontal=True,
        key="stock_view_mode",
        index=0  # Default to grouped view
    )
    
    if view_mode == "Grouped by GRN":
        grouped_data = fetch_json("stock/by-grn")
        if grouped_data and grouped_data.get("grouped_by_grn"):
            st.subheader(f"Passed GRNs ({grouped_data.get('total_grns', 0)} GRNs)")
            st.caption("Stock movements grouped by GRN reference - only quality passed items")
            
            for grn_group in grouped_data["grouped_by_grn"]:
                with st.expander(
                    f"📦 **{grn_group['grn_reference']}** - Total Quantity: **{grn_group['total_qty']}** units",
                    expanded=False
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**GRN Reference:** {grn_group['grn_reference']}")
                        st.write(f"**Total Items:** {len(grn_group['items'])}")
                    with col2:
                        st.write(f"**Total Quantity:** {grn_group['total_qty']} units")
                        if grn_group.get('created_at'):
                            st.write(f"**Date:** {grn_group['created_at']}")
                    
                    st.divider()
                    st.write("**Items in this GRN:**")
                    items_df = [
                        {
                            "Item Name": item["item_name"],
                            "Quantity": item["qty"],
                            "Type": item["movement_type"],
                            "Date": item.get("created_at", "N/A"),
                        }
                        for item in grn_group["items"]
                    ]
                    if items_df:
                        st.dataframe(items_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stock movements found. Stock is only recorded for quality passed items.")
    else:
        # List view with search
        params = {"search": search_term} if search_term else None
        ledger = fetch_json("stock", params=params)
        if ledger:
            # Format for better display
            display_data = [
                {
                    "Item Name": entry.get("item_name", "Unknown"),
                    "Quantity": entry.get("qty", 0),
                    "GRN Reference": entry.get("reference", "N/A"),
                    "Movement Type": entry.get("movement_type", "GRN"),
                    "Date": entry.get("created_at", "N/A"),
                }
                for entry in ledger
            ]
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        else:
            st.info("No stock movements found.")


def show_disputes():
    st.markdown("## ⚠️ Disputes & Anomalies")
    st.markdown("---")
    disputes = fetch_json("disputes")
    if disputes:
        # Filter by status
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Open", "Resolved"],
            key="dispute_status_filter"
        )
        
        filtered_disputes = disputes
        if status_filter == "Open":
            filtered_disputes = [d for d in disputes if d.get("status") == "open"]
        elif status_filter == "Resolved":
            filtered_disputes = [d for d in disputes if d.get("status") == "resolved"]
        
        if not filtered_disputes:
            st.info(f"No {status_filter.lower()} disputes found.")
            return
        
        for dispute in filtered_disputes:
            status = dispute.get("status", "unknown")
            status_color = "🟢" if status == "resolved" else "🔴"
            dispute_id = dispute.get("_id", {}).get("$oid") if isinstance(dispute.get("_id"), dict) else dispute.get("_id")
            
            with st.expander(
                f"{status_color} **{dispute['issue_type']}** (Line {dispute['line_id']}) - {status.upper()}",
                expanded=status == "open"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**PO ID:** {dispute['po_id']}")
                    st.write(f"**GRN Reference:** {dispute.get('grn_reference', dispute.get('grn_id', 'N/A'))}")
                with col2:
                    st.write(f"**Status:** {dispute.get('status', 'unknown')}")
                    if dispute.get("resolved_at"):
                        st.write(f"**Resolved:** {dispute['resolved_at']}")
                
                st.divider()
                st.write(f"**Issue Description:**")
                st.write(dispute['message'])  # This already contains detailed information
                
                # Show excess quantity for over-delivery
                if dispute.get("excess_qty", 0) > 0:
                    st.warning(f"⚠️ **Excess Quantity to Return:** {dispute['excess_qty']} units")
                    st.info(f"📦 You should return **{dispute['excess_qty']}** product(s) to the supplier.")
                
                st.caption(f"Created: {dispute.get('created_at', 'N/A')}")
                
                # Action buttons for open disputes
                if status == "open" and dispute_id:
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Validate/Resolve", key=f"resolve_{dispute_id}", use_container_width=True):
                            try:
                                result = post_json(f"disputes/{dispute_id}/resolve", {})
                                if result:
                                    st.success("Dispute resolved successfully!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error resolving dispute: {e}")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{dispute_id}", use_container_width=True, type="secondary"):
                            try:
                                # Use DELETE request
                                import requests
                                response = requests.delete(
                                    f"{API_BASE_URL}/disputes/{dispute_id}",
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    st.success("Dispute deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting dispute: {response.text}")
                            except Exception as e:
                                st.error(f"Error deleting dispute: {e}")
    else:
        st.write("No disputes logged yet.")


def main():
    set_page_defaults()
    st.sidebar.markdown("### Navigation")
    selection = st.sidebar.radio(
        "Select Page",
        ["Dashboard", "Create PO", "Create GRN", "Stock Ledger", "View Disputes"],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")

    if selection == "Dashboard":
        show_dashboard()
    elif selection == "Create PO":
        show_po_creator()
    elif selection == "Create GRN":
        show_grn_creator()
    elif selection == "Stock Ledger":
        show_stock_ledger()
    elif selection == "View Disputes":
        show_disputes()



if __name__ == "__main__":
    main()

