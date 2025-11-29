// API Base URL
const API_URL = "http://localhost:8000";
const WORKFLOW_URL = "http://localhost:8001";

// Status workflow mapping
const statusWorkflow = {
    "Brouillon": ["En cours d'approbation"],
    "En cours d'approbation": ["Approuvé", "Rejeté"],
    "Approuvé": ["Emis"],
    "Rejeté": [],
    "Emis": ["Confirmé"],
    "Confirmé": ["Livré partiellement", "Livré totalement", "En anomalie"],
    "Livré partiellement": ["Livré totalement"],
    "Livré totalement": ["Clôturé"],
    "En anomalie": ["Confirmé"],
    "Clôturé": []
};

// Status colors
const statusColors = {
    "Validated": "#10b981",
    "En conversion PO": "#f59e0b",
    "Brouillon": "#6b7280",
    "En cours d'approbation": "#3b82f6",
    "Approuvé": "#10b981",
    "Rejeté": "#ef4444",
    "Emis": "#8b5cf6",
    "Confirmé": "#10b981",
    "Livré partiellement": "#f97316",
    "Livré totalement": "#10b981",
    "En anomalie": "#ef4444",
    "Clôturé": "#6b7280"
};

/* -------------------------
   Reconnecting WebSocket
   - reconnects with exponential backoff
   - safe handlers (no uncaught exceptions)
   ------------------------- */
class ReconnectingWebSocket {
    constructor(url, name, onMessage) {
        this.url = url;
        this.name = name || url;
        this.onMessage = onMessage || function(){};
        this.ws = null;
        this.forcedClose = false;
        this.t = 1000; // initial backoff (ms)
        this.maxBackoff = 30000;
        this.connect();
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);
        } catch (e) {
            console.error(`${this.name} - WebSocket ctor error:`, e);
            this.scheduleReconnect();
            return;
        }

        this.ws.onopen = (ev) => {
            console.info(`${this.name} connected`);
            this.setStatus(true);
            // reset backoff
            this.t = 1000;
        };

        this.ws.onmessage = (ev) => {
            try {
                const data = (() => {
                    try { return JSON.parse(ev.data); } catch(_) { return ev.data; }
                })();
                this.onMessage(data, this.name);
            } catch (err) {
                console.error(`${this.name} message handler error:`, err);
                // swallow so the whole script doesn't crash
            }
        };

        this.ws.onerror = (ev) => {
            console.warn(`${this.name} websocket error`, ev);
            this.setStatus(false);
            // errors are handled by onclose/reconnect
        };

        this.ws.onclose = (ev) => {
            console.warn(`${this.name} websocket closed`, ev && ev.code);
            this.setStatus(false);
            if (!this.forcedClose) this.scheduleReconnect();
        };
    }

    scheduleReconnect() {
        const delay = this.t;
        console.info(`${this.name} reconnecting in ${delay}ms`);
        setTimeout(() => {
            // increase backoff
            this.t = Math.min(this.t * 1.8, this.maxBackoff);
            this.connect();
        }, delay);
    }

    send(obj) {
        try {
            const data = typeof obj === "string" ? obj : JSON.stringify(obj);
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(data);
                return true;
            } else {
                console.warn(`${this.name} send failed - socket not open`);
                return false;
            }
        } catch (err) {
            console.error(`${this.name} send error:`, err);
            return false;
        }
    }

    close() {
        this.forcedClose = true;
        if (this.ws) this.ws.close();
    }

    setStatus(connected) {
        // optional: update DOM element to reflect ws status
        // example: element id = 'ws-status-module3' or 'ws-status-module4'
        const el = document.getElementById(this.name === 'module3' ? 'ws-status-module3' : 'ws-status-module4');
        if (el) {
            el.textContent = connected ? 'Connected' : 'Disconnected';
            el.style.color = connected ? '#10b981' : '#ef4444';
        }
    }
}

/* -------------------------
   Global WS handlers
   ------------------------- */
function handleIncomingMessage(data, origin) {
    // data is either parsed JSON or raw string
    // keep this resilient: don't throw
    try {
        // if the message is a string, try to parse
        const payload = (typeof data === 'string') ? (() => {
            try { return JSON.parse(data); } catch { return { type: 'raw', raw: data }; }
        })() : data;

        // Accept a few known types and trigger UI refreshes
        if (!payload || !payload.type) {
            // unknown, ignore but log
            console.debug(`${origin} - unknown message`, payload);
            return;
        }

        switch (payload.type) {
            case 'pr_created':
            case 'pr_updated':
                // reload PRs
                loadPRs();
                break;
            case 'po_created':
            case 'po_updated':
            case 'workflow_completed':
                // a PO or workflow changed: reload POs and PRs
                loadPOs();
                loadPRs();
                break;
            case 'workflow_created':
            case 'workflow_updated':
                // workflow changes: refresh POs (may contain workflow_id) and optionally call workflow UI if open
                loadPOs();
                break;
            case 'comment_added':
                // if you have a workflow UI open, you could append the comment; otherwise refresh
                loadPOs();
                break;
            default:
                console.debug(`${origin} - unhandled message type`, payload.type);
        }
    } catch (err) {
        console.error("handleIncomingMessage error:", err);
    }
}

/* -------------------------
   Initialize WebSockets
   - module3WS : listens for PR/PO changes
   - module4WS : listens for workflow events
   ------------------------- */
const module3WS = new ReconnectingWebSocket("ws://localhost:8000/ws", "module3", handleIncomingMessage);
const module4WS = new ReconnectingWebSocket("ws://localhost:8001/ws", "module4", handleIncomingMessage);

/* -------------------------
   Existing app functions (unchanged, with minor robustness)
   ------------------------- */

// Load PR list
async function loadPRs() {
    try {
        const res = await fetch(`${API_URL}/prs`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const prs = await res.json();

        const tbody = document.querySelector("#pr-table tbody");
        const prSelect = document.getElementById("prId");

        if (tbody) tbody.innerHTML = "";
        if (prSelect) prSelect.innerHTML = '<option value="">Sélectionner PR</option>';

        prs.forEach(pr => {
            const statusColor = statusColors[pr.status] || "#6b7280";
            const row = document.createElement('tr');

            row.innerHTML = `
                <td><strong>${pr.id}</strong></td>
                <td>${pr.requester}</td>
                <td>${pr.department}</td>
                <td>${pr.items}</td>
                <td>${pr.date}</td>
                <td><span style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">${pr.status}</span></td>
                <td>${pr.status === 'Validated' ? `<button onclick="preparePO('${pr.id}', '${escapeHtml(pr.items)}')">Créer PO</button>` : '-'}</td>
            `;

            if (tbody) tbody.appendChild(row);

            if (pr.status === 'Validated' && prSelect) {
                const opt = document.createElement('option');
                opt.value = pr.id;
                opt.textContent = `${pr.id} - ${pr.items}`;
                prSelect.appendChild(opt);
            }
        });
    } catch (error) {
        console.error("Error loading PRs:", error);
        // do not block UI; only notify once
        // optionally show a small banner instead of alert to avoid being intrusive
        // alert("❌ Erreur de connexion au serveur. Vérifiez que FastAPI est lancé.");
    }
}

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

// Pre-fill PO form
function preparePO(id, items) {
    const prEl = document.getElementById("prId");
    const itemsEl = document.getElementById("items");
    if (prEl) prEl.value = id;
    if (itemsEl) itemsEl.value = items;
    const sec = document.querySelector('section:nth-child(2)');
    if (sec) sec.scrollIntoView({ behavior: 'smooth' });
}

// Handle PO creation
const poForm = document.getElementById("po-form");
if (poForm) {
    poForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            prId: document.getElementById("prId").value,
            supplier: document.getElementById("supplier").value,
            items: document.getElementById("items").value,
            quantity: parseInt(document.getElementById("quantity").value),
            unitPrice: parseFloat(document.getElementById("unitPrice").value),
            tax: 19.0,
            delivery: document.getElementById("delivery").value
        };

        try {
            const res = await fetch(`${API_URL}/pos`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                alert(`✅ PO créé avec succès!\n📋 ID: ${data.id}\n🔄 Workflow d'approbation lancé automatiquement!`);
                poForm.reset();
                loadPOs();
                loadPRs();
            } else {
                // Better error handling
                let errorMessage = "Erreur inconnue";
                try {
                    const errorData = await res.json();
                    errorMessage = errorData.detail || JSON.stringify(errorData);
                } catch (parseError) {
                    errorMessage = `HTTP ${res.status}: ${res.statusText}`;
                }
                alert(`❌ Erreur: ${errorMessage}`);
            }
        } catch (error) {
            console.error("Error creating PO:", error);
            alert("❌ Erreur de connexion — vérifiez que le serveur est démarré.");
        }
    });
}

// Load PO list
async function loadPOs() {
    try {
        const res = await fetch(`${API_URL}/pos`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const pos = await res.json();

        const tbody = document.querySelector("#po-table tbody");
        if (tbody) tbody.innerHTML = "";

        pos.forEach(po => {
            const statusColor = statusColors[po.status] || "#6b7280";
            const nextStatuses = statusWorkflow[po.status] || [];

            let actionButtons = '';

            // Add workflow link if exists
            if (po.workflow_id) {
                actionButtons += `
                    <a href="../erp - 4/ui.html?workflow=${po.workflow_id}" 
                    target="_blank"
                    style="display: inline-block; padding: 6px 12px; background: #3b82f6; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; margin-right: 5px;">
                        📋 Voir Approbations
                    </a>
                `;
            }

            // Add status change dropdown
            if (nextStatuses.length > 0) {
                actionButtons += `<select onchange="updateStatus('${po.id}', this.value)" style="padding: 6px; border: 1px solid #ccc; border-radius: 4px;"><option value="">Changer statut...</option>${nextStatuses.map(s => `<option value="${s}">${s}</option>`).join('')}</select>`;
            } else if (!po.workflow_id) {
                actionButtons = '<span style="color: #6b7280;">-</span>';
            }

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${po.id}</strong></td>
                <td>${po.prId}</td>
                <td>${po.supplier}</td>
                <td><strong>${po.amount.toFixed(2)} TND</strong></td>
                <td>${po.date}</td>
                <td>
                    <span style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        ${po.status}
                    </span>
                    ${po.workflow_id ? `<br><small style="color: #6b7280;">🔄 ${po.workflow_id}</small>` : ''}
                </td>
                <td>${actionButtons}</td>
            `;
            if (tbody) tbody.appendChild(row);
        });
    } catch (error) {
        console.error("Error loading POs:", error);
    }
}

// Update PO status
async function updateStatus(id, status) {
    if (!status) return;

    try {
        const res = await fetch(`${API_URL}/pos/${id}/status`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({status})
        });

        if (res.ok) {
            alert(`✅ Statut mis à jour: ${status}`);
            loadPOs();
            // optimistically notify WS peers
            module3WS.send({ type: "po_updated", data: { id, status } });
        } else {
            const error = await res.json();
            alert(`❌ Erreur: ${error.detail || JSON.stringify(error)}`);
        }
    } catch (error) {
        console.error("Error updating status:", error);
        alert("❌ Erreur de connexion — vérifiez la liste des PO.");
        setTimeout(loadPOs, 500);
    }
}

// Load statistics
async function loadStats() {
    try {
        const res = await fetch(`${API_URL}/stats`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const stats = await res.json();
        console.log("📊 Statistics:", stats);
    } catch (error) {
        console.error("Error loading stats:", error);
    }
}

/* -------------------------
   Initialize UI
   ------------------------- */
loadPRs();
loadPOs();
loadStats();
