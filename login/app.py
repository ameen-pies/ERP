# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import time
import os

try:
    from database import create_user, authenticate_user
    DB_CONNECTED = True
except Exception as e:
    st.error(f"Database connection error: {e}")
    DB_CONNECTED = False

# Page configuration
st.set_page_config(
    page_title="ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None


def show_dashboard():
    """Display the dashboard using index.html"""
    
    # Read index.html
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(current_dir, "index.html")
        
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Get user data
        user_data = st.session_state.get('user_data', {})
        user_role = user_data.get('role', 'user')
        user_name = user_data.get('full_name', 'User')
        
        # Inject user data directly into the JavaScript
        html_content = html_content.replace(
            "const userRole = urlParams.get('role') || 'user';",
            f"const userRole = '{user_role}';"
        )
        html_content = html_content.replace(
            "const userName = urlParams.get('name') || 'User';",
            f"const userName = '{user_name}';"
        )
        
        # Inject logout handler that redirects back to login
        logout_script = """
        <script>
            function logout() {
                if (confirm('Are you sure you want to logout?')) {
                    localStorage.clear();
                    // Tell parent window to logout
                    window.parent.postMessage({type: 'logout'}, '*');
                }
            }
            
            // Listen for logout command from parent
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === 'logout') {
                    localStorage.clear();
                }
            });
        </script>
        """
        html_content = html_content.replace('</body>', logout_script + '</body>')
        
        # Hide Streamlit UI
        st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding: 0 !important; max-width: 100% !important;}
            iframe {border: none !important;}
        </style>
        """, unsafe_allow_html=True)
        
        # Display the dashboard
        components.html(html_content, height=900, scrolling=True)
        
        # Listen for logout message from iframe
        st.markdown("""
        <script>
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === 'logout') {
                    // Trigger Streamlit rerun by clicking hidden button
                    const logoutBtn = window.parent.document.querySelector('[data-testid="baseButton-secondary"]');
                    if (logoutBtn) logoutBtn.click();
                }
            });
        </script>
        """, unsafe_allow_html=True)
        
        # Hidden logout button that will be triggered
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Logout", key="backup_logout", type="secondary"):
                st.session_state.authenticated = False
                st.session_state.user_data = None
                st.rerun()
            
    except FileNotFoundError:
        st.error(f"❌ index.html not found at: {index_path}")
        if st.button("← Back to Login"):
            st.session_state.authenticated = False
            st.rerun()


def show_login():
    """Display login HTML page"""
    
    # Check for query parameters (for form submission)
    query_params = st.query_params
    
    # Handle login submission
    if 'login_email' in query_params and 'login_password' in query_params:
        email = query_params['login_email']
        password = query_params['login_password']
        
        with st.spinner("🔐 Authenticating..."):
            result = authenticate_user(email, password)
            
            if result["success"]:
                st.session_state.authenticated = True
                st.session_state.user_data = result['user']
                # Clear query params and rerun
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
    
    # Handle signup submission
    if 'signup_name' in query_params:
        name = query_params.get('signup_name', '')
        email = query_params.get('signup_email', '')
        dept = query_params.get('signup_dept', '')
        role = query_params.get('signup_role', '')
        password = query_params.get('signup_password', '')
        
        with st.spinner("🔐 Creating account..."):
            result = create_user(name, email, dept, role, password)
            
            if result["success"]:
                st.success(f"✅ Account created successfully! Please sign in.")
                st.balloons()
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
    
    # Hide Streamlit UI
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0 !important; max-width: 100% !important;}
    </style>
    """, unsafe_allow_html=True)
    
    # Login HTML page
    login_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f0f2f5;
                display: flex;
                min-height: 100vh;
                overflow-y: auto;
            }
            
            .container {
                display: flex;
                width: 100%;
                gap: 3rem;
                padding: 3rem;
                min-height: 100vh;
            }
            
            .brand-section {
                flex: 1;
                background: linear-gradient(135deg, #4169E1 0%, #1E40AF 100%);
                border-radius: 24px;
                padding: 4rem;
                color: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 10px 40px rgba(65, 105, 225, 0.3);
            }
            
            .brand-logo {
                font-size: 2rem;
                font-weight: 600;
                margin-bottom: 2.5rem;
                display: flex;
                align-items: center;
                gap: 0.65rem;
            }
            
            .brand-title {
                font-size: 2.5rem;
                font-weight: 600;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .brand-description {
                font-size: 1rem;
                opacity: 0.95;
                margin-bottom: 2rem;
                line-height: 1.5;
            }
            
            .feature-item {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
                background: rgba(255, 255, 255, 0.12);
                padding: 1rem;
                border-radius: 10px;
                font-size: 0.95rem;
                backdrop-filter: blur(10px);
            }
            
            .feature-icon {
                font-size: 1.5rem;
            }
            
            .login-section {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem 0;
            }
            
            .login-card {
                background: white;
                border-radius: 24px;
                padding: 4rem 3.5rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                width: 100%;
                max-width: 650px;
                border: 1px solid #e5e7eb;
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .login-title {
                font-size: 2.5rem;
                color: #111827;
                margin-bottom: 0.75rem;
                font-weight: 600;
            }
            
            .login-subtitle {
                color: #6b7280;
                font-size: 1.15rem;
            }
            
            .form-group {
                margin-bottom: 2rem;
            }
            
            label {
                display: block;
                font-size: 1.05rem;
                font-weight: 500;
                color: #374151;
                margin-bottom: 0.75rem;
            }
            
            input, select {
                width: 100%;
                padding: 1.1rem 1.25rem;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                font-size: 1.05rem;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                transition: all 0.2s ease;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: #4169E1;
                box-shadow: 0 0 0 3px rgba(65, 105, 225, 0.1);
            }
            
            .btn-submit {
                width: 100%;
                padding: 1.15rem;
                background: linear-gradient(135deg, #4169E1 0%, #1E40AF 100%);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                margin-top: 1.5rem;
                transition: all 0.3s ease;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            .btn-submit:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(65, 105, 225, 0.3);
            }
            
            .btn-submit:active {
                transform: translateY(0);
            }
            
            .btn-submit:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .tabs {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 2.5rem;
                background: transparent;
                padding: 0;
                border-radius: 0;
                justify-content: center;
            }
            
            .tab {
                padding: 0.65rem 2rem;
                background: transparent;
                border: none;
                color: #9ca3af;
                font-weight: 500;
                cursor: pointer;
                border-radius: 0;
                transition: all 0.2s ease;
                font-size: 0.95rem;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                border-bottom: 2px solid transparent;
            }
            
            .tab.active {
                background: transparent;
                color: #2563eb;
                box-shadow: none;
                border-bottom-color: #2563eb;
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .checkbox-label {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                font-size: 1rem;
                cursor: pointer;
                color: #374151;
            }
            
            input[type="checkbox"] {
                width: auto;
                cursor: pointer;
                width: 18px;
                height: 18px;
            }
            
            @media (max-width: 1024px) {
                .container {
                    flex-direction: column;
                    gap: 2rem;
                }
                
                .brand-section {
                    padding: 3rem;
                }
                
                .brand-title {
                    font-size: 2.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="brand-section">
                <div>
                    <div class="brand-logo">
                        <span>🏢</span>
                        <span>ePurchase</span>
                    </div>
                    <div class="brand-title">Welcome to Your ERP Platform</div>
                    <div class="brand-description">Streamline your business operations with our comprehensive procurement management solution.</div>
                    <div class="feature-item">
                        <span class="feature-icon">🔒</span>
                        <span>Secure and reliable access control</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🏢</span>
                        <span>Multi-department management</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📊</span>
                        <span>Real-time analytics and insights</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">⚡</span>
                        <span>Fast and efficient workflows</span>
                    </div>
                </div>
            </div>
            
            <div class="login-section">
                <div class="login-card">
                    <div class="login-header">
                        <div class="login-title" id="form-title">Sign In</div>
                        <div class="login-subtitle" id="form-subtitle">Access your dashboard</div>
                    </div>
                    
                    <div class="tabs">
                        <button class="tab active" onclick="switchTab('login')">Sign In</button>
                        <button class="tab" onclick="switchTab('signup')">Sign Up</button>
                    </div>
                    
                    <!-- Login Tab -->
                    <div id="login-tab" class="tab-content active">
                        <form onsubmit="handleLogin(event)">
                            <div class="form-group">
                                <label>Email Address</label>
                                <input type="email" id="login-email" placeholder="your.email@company.com" required>
                            </div>
                            
                            <div class="form-group">
                                <label>Password</label>
                                <input type="password" id="login-password" placeholder="••••••••" required>
                            </div>
                            
                            <button type="submit" class="btn-submit">Sign In</button>
                        </form>
                    </div>
                    
                    <!-- Signup Tab -->
                    <div id="signup-tab" class="tab-content">
                        <form onsubmit="handleSignup(event)">
                            <div class="form-group">
                                <label>Full Name</label>
                                <input type="text" id="signup-name" placeholder="John Doe" required>
                            </div>
                            
                            <div class="form-group">
                                <label>Email Address</label>
                                <input type="email" id="signup-email" placeholder="your.email@company.com" required>
                            </div>
                            
                            <div class="form-group">
                                <label>Department</label>
                                <select id="signup-dept" required>
                                    <option value="">Select Department</option>
                                    <option value="Finance">Finance</option>
                                    <option value="Human Resources">Human Resources</option>
                                    <option value="Operations">Operations</option>
                                    <option value="Sales">Sales</option>
                                    <option value="IT">IT</option>
                                    <option value="Marketing">Marketing</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>Role</label>
                                <select id="signup-role" required>
                                    <option value="user">Department User</option>
                                    <option value="head">Department Head</option>
                                    <option value="treasurer">Treasurer</option>
                                    <option value="admin">Administrator</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>Password</label>
                                <input type="password" id="signup-password" placeholder="••••••••" required minlength="6">
                            </div>
                            
                            <div class="form-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="signup-terms" required>
                                    I agree to Terms and Conditions
                                </label>
                            </div>
                            
                            <button type="submit" class="btn-submit">Create Account</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                const titleEl = document.getElementById('form-title');
                const subtitleEl = document.getElementById('form-subtitle');
                
                if (tab === 'login') {
                    document.querySelectorAll('.tab')[0].classList.add('active');
                    document.getElementById('login-tab').classList.add('active');
                    titleEl.textContent = 'Sign In';
                    subtitleEl.textContent = 'Access your dashboard';
                } else {
                    document.querySelectorAll('.tab')[1].classList.add('active');
                    document.getElementById('signup-tab').classList.add('active');
                    titleEl.textContent = 'Create Account';
                    subtitleEl.textContent = 'Get started with ePurchase';
                }
            }
            
            function handleLogin(event) {
                event.preventDefault();
                
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                
                // Redirect to same page with query parameters
                window.location.href = `?login_email=${encodeURIComponent(email)}&login_password=${encodeURIComponent(password)}`;
            }
            
            function handleSignup(event) {
                event.preventDefault();
                
                const name = document.getElementById('signup-name').value;
                const email = document.getElementById('signup-email').value;
                const dept = document.getElementById('signup-dept').value;
                const role = document.getElementById('signup-role').value;
                const password = document.getElementById('signup-password').value;
                
                // Redirect to same page with query parameters
                window.location.href = `?signup_name=${encodeURIComponent(name)}&signup_email=${encodeURIComponent(email)}&signup_dept=${encodeURIComponent(dept)}&signup_role=${encodeURIComponent(role)}&signup_password=${encodeURIComponent(password)}`;
            }
        </script>
    </body>
    </html>
    """
    
    # Display login page
    components.html(login_html, height=1000, scrolling=True)


def main():
    if st.session_state.authenticated:
        show_dashboard()
    else:
        show_login()


if __name__ == "__main__":
    main()