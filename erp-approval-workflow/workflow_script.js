const API_URL = "http://localhost:8001";
let CURRENT_USER_ID = "user_1";

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadPendingApprovals();
    loadUsersForDelegation();
    setupEventListeners();
    handleUrlParameters(); // Add this line
    
    // Set current user based on initiator selection
    document.getElementById('initiator').addEventListener('change', function() {
        CURRENT_USER_ID = this.value;
        const userName = this.options[this.selectedIndex].text.split(' (')[0];
        document.getElementById('current-user').textContent = `Utilisateur: ${userName}`;
        loadPendingApprovals();
    });
});

// Handle URL parameters for direct workflow access
function handleUrlParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    const workflowId = urlParams.get('workflow');
    
    if (workflowId) {
        // Auto-load the workflow if ID is provided in URL
        console.log('Loading workflow from URL:', workflowId);
        viewWorkflowDetail(workflowId);
    }
}

function setupEventListeners() {
    // Create workflow form
    document.getElementById('create-workflow-form').addEventListener('submit', createWorkflow);
    
    // Action form
    document.getElementById('workflow-action-form').addEventListener('submit', submitWorkflowAction);
    
    // Action selection change
    document.getElementById('action-select').addEventListener('change', function() {
        const delegateSection = document.getElementById('delegate-section');
        delegateSection.style.display = this.value === 'delegate' ? 'block' : 'none';
    });
}

// Create new workflow
async function createWorkflow(e) {
    e.preventDefault();
    
    const formData = {
        document_type: document.getElementById('document-type').value,
        document_id: document.getElementById('document-id').value,
        document_title: document.getElementById('document-title').value,
        initiator: document.getElementById('initiator').value,
        initiator_name: document.getElementById('initiator').options[document.getElementById('initiator').selectedIndex].text.split(' (')[0],
        department: document.getElementById('department').value,
        total_amount: parseFloat(document.getElementById('total-amount').value) || 0
    };
    
    try {
        const res = await fetch(`${API_URL}/workflows`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (res.ok) {
            const workflow = await res.json();
            alert(`✅ Workflow créé avec succès! ID: ${workflow.workflow_id}`);
            document.getElementById('create-workflow-form').reset();
            loadPendingApprovals();
        } else {
            const error = await res.json();
            alert(`❌ Erreur: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error creating workflow:', error);
        alert('❌ Erreur de connexion au serveur');
    }
}

// Load pending approvals for current user
async function loadPendingApprovals() {
    try {
        const res = await fetch(`${API_URL}/workflows/user/${CURRENT_USER_ID}/pending`);
        const workflows = await res.json();

        const tbody = document.querySelector("#pending-approvals-table tbody");
        tbody.innerHTML = "";

        let pendingCount = 0;
        let completedCount = 0;
        let overdueCount = 0;

        workflows.forEach(workflow => {
            const currentStep = workflow.steps.find(step => 
                step.status === 'in_progress' || step.status === 'pending'
            );
            
            const isAssignedToMe = currentStep && currentStep.assigned_to === CURRENT_USER_ID;
            
            if (isAssignedToMe) {
                pendingCount++;
                
                // Check if overdue
                const deadline = new Date(currentStep.deadline);
                const today = new Date();
                if (deadline < today) overdueCount++;

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${workflow.workflow_id}</strong></td>
                        <td>${workflow.document_title}</td>
                        <td>${workflow.initiator_name}</td>
                        <td>${workflow.department}</td>
                        <td>${workflow.total_amount ? workflow.total_amount.toFixed(2) + ' TND' : 'N/A'}</td>
                        <td>${currentStep ? currentStep.role : 'N/A'}</td>
                        <td style="color: ${deadline < today ? '#ef4444' : '#6b7280'}">
                            ${new Date(currentStep.deadline).toLocaleDateString()}
                        </td>
                        <td>
                            <button onclick="viewWorkflowDetail('${workflow.workflow_id}')" class="btn-primary">
                                👁️ Voir
                            </button>
                        </td>
                    </tr>
                `;
            }
        });

        // Update metrics
        document.getElementById('pending-count').textContent = pendingCount;
        document.getElementById('completed-count').textContent = completedCount;
        document.getElementById('overdue-count').textContent = overdueCount;

        if (pendingCount === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 20px; color: #6b7280;">
                        🎉 Aucune validation en attente !
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error("Error loading pending approvals:", error);
    }
}

// View workflow details
async function viewWorkflowDetail(workflowId) {
    try {
        const res = await fetch(`${API_URL}/workflows/${workflowId}`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const workflow = await res.json();

        // Update UI
        document.getElementById('workflow-title').textContent = workflow.document_title;
        document.getElementById('current-workflow-id').value = workflowId;
        
        // Load progress
        const progressRes = await fetch(`${API_URL}/workflows/${workflowId}/progress`);
        if (progressRes.ok) {
            const progress = await progressRes.json();
            document.getElementById('progress-percentage').textContent = 
                `${Math.round(progress.progress_percentage)}%`;
            document.getElementById('progress-fill').style.width = 
                `${progress.progress_percentage}%`;
        }

        // Render approval steps
        renderApprovalSteps(workflow);
        
        // Load comments
        loadComments(workflowId);
        
        // Show detail section
        document.getElementById('workflow-detail').style.display = 'block';
        document.getElementById('workflow-detail').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error("Error loading workflow details:", error);
        alert("❌ Erreur lors du chargement du workflow: " + error.message);
    }
}

// Render approval steps
function renderApprovalSteps(workflow) {
    const container = document.getElementById('approval-steps');
    container.innerHTML = '';

    workflow.steps.forEach((step, index) => {
        const stepClass = getStepClass(step, workflow.current_step);
        const statusText = getStatusText(step.status);
        const statusColor = getStatusColor(step.status);
        
        const isCurrentStep = index === workflow.current_step;
        const isAssignedToMe = step.assigned_to === CURRENT_USER_ID && isCurrentStep;

        container.innerHTML += `
            <div class="approval-step ${stepClass}">
                <div class="step-status" style="background: ${statusColor}">
                    ${statusText}
                </div>
                <h4>Étape ${index + 1}: ${step.role}</h4>
                <p><strong>Assigné à:</strong> ${step.assigned_name}</p>
                ${step.deadline ? `<p><strong>Délai:</strong> ${new Date(step.deadline).toLocaleDateString()}</p>` : ''}
                ${step.comments ? `<p><strong>Commentaires:</strong> ${step.comments}</p>` : ''}
                ${step.action_date ? `<p><strong>Action le:</strong> ${new Date(step.action_date).toLocaleString()}</p>` : ''}
                
                ${isAssignedToMe && step.status === 'in_progress' ? `
                    <div class="action-buttons">
                        <button onclick="showActionForm('${workflow.workflow_id}', '${step.step_id}')" 
                                class="btn-primary">
                            📝 Prendre Action
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    });
}

// Helper functions
function getStepClass(step, currentStepIndex) {
    if (step.status === 'approved') return 'approved';
    if (step.status === 'rejected') return 'rejected';
    if (step.status === 'in_progress') return 'current';
    return '';
}

function getStatusText(status) {
    const statusMap = {
        'pending': 'En attente',
        'in_progress': 'En cours',
        'approved': 'Approuvé',
        'rejected': 'Rejeté',
        'changes_requested': 'Modifications demandées'
    };
    return statusMap[status] || status;
}

function getStatusColor(status) {
    const colorMap = {
        'pending': '#6b7280',
        'in_progress': '#3b82f6',
        'approved': '#10b981',
        'rejected': '#ef4444',
        'changes_requested': '#f59e0b'
    };
    return colorMap[status] || '#6b7280';
}

// Show action form
function showActionForm(workflowId, stepId) {
    document.getElementById('current-workflow-id').value = workflowId;
    document.getElementById('current-step-id').value = stepId;
    document.getElementById('action-form').style.display = 'block';
    document.getElementById('action-form').scrollIntoView({ behavior: 'smooth' });
}

// Hide action form
function hideActionForm() {
    document.getElementById('action-form').style.display = 'none';
    document.getElementById('workflow-action-form').reset();
    document.getElementById('delegate-section').style.display = 'none';
}

// Submit workflow action
async function submitWorkflowAction(e) {
    e.preventDefault();
    
    const workflowId = document.getElementById('current-workflow-id').value;
    const stepId = document.getElementById('current-step-id').value;
    const action = document.getElementById('action-select').value;
    const comments = document.getElementById('action-comments').value;
    const delegateTo = document.getElementById('delegate-to').value;

    const payload = {
        step_id: stepId,
        action: action,
        comments: comments
    };

    if (action === 'delegate' && delegateTo) {
        payload.delegate_to = delegateTo;
    }

    try {
        const res = await fetch(`${API_URL}/workflows/${workflowId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert('✅ Action enregistrée avec succès !');
            hideActionForm();
            viewWorkflowDetail(workflowId);
            loadPendingApprovals();
        } else {
            const error = await res.json();
            alert(`❌ Erreur: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error submitting action:', error);
        alert('❌ Erreur de connexion');
    }
}

// Load users for delegation
async function loadUsersForDelegation() {
    try {
        const res = await fetch(`${API_URL}/users`);
        const users = await res.json();
        
        const select = document.getElementById('delegate-to');
        select.innerHTML = '<option value="">Sélectionner un utilisateur</option>';
        
        for (const [userId, userData] of Object.entries(users)) {
            if (userId !== CURRENT_USER_ID) {
                select.innerHTML += `
                    <option value="${userId}">${userData.name} (${userData.department})</option>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Load comments
async function loadComments(workflowId) {
    try {
        const res = await fetch(`${API_URL}/workflows/${workflowId}/comments`);
        const comments = await res.json();
        
        const container = document.getElementById('comments-thread');
        container.innerHTML = '';
        
        if (comments.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #6b7280;">Aucun commentaire pour le moment</p>';
            return;
        }
        
        // Sort comments by timestamp
        comments.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        comments.forEach(comment => {
            container.innerHTML += `
                <div class="comment">
                    <div class="comment-author">${comment.author_name}</div>
                    <div class="comment-time">${new Date(comment.timestamp).toLocaleString()}</div>
                    <div class="comment-message">${comment.message}</div>
                </div>
            `;
        });
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

// Add new comment
async function addComment() {
    const workflowId = document.getElementById('current-workflow-id').value;
    const message = document.getElementById('new-comment').value;
    
    if (!message.trim()) {
        alert('Veuillez saisir un message');
        return;
    }
    
    // Get current user info
    const userResponse = await fetch(`${API_URL}/users`);
    const users = await userResponse.json();
    const currentUser = users[CURRENT_USER_ID];
    
    const payload = {
        workflow_id: workflowId,
        author: CURRENT_USER_ID,
        author_name: currentUser.name,
        message: message
    };
    
    try {
        const res = await fetch(`${API_URL}/workflows/${workflowId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            document.getElementById('new-comment').value = '';
            loadComments(workflowId);
        } else {
            const error = await res.json();
            alert(`❌ Erreur: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        alert('❌ Erreur de connexion');
    }
}