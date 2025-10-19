"""
Code-Monitor Streamlit Dashboard (MVP)
"""
import streamlit as st
import requests
import pandas as pd
from datetime import date

# Configuration
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Code-Monitor Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Code-Monitor Dashboard")
st.markdown("**Lab Knowledge Distillation & Productivity Monitoring System**")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Home", "👥 Users", "➕ Add User", "📊 Status"]
    )

# Page: Home
if page == "🏠 Home":
    st.header("Welcome to Code-Monitor")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Users", "0", "Loading...")
    with col2:
        st.metric("This Week Submissions", "0")
    with col3:
        st.metric("System Status", "🟢 Running")

    st.markdown("---")
    st.subheader("Quick Links")
    st.markdown("""
    - **API Documentation**: http://localhost:8000/docs
    - **Health Check**: http://localhost:8000/health
    - **GitHub**: https://github.com/your-lab/code-monitor
    """)

# Page: Users
elif page == "👥 Users":
    st.header("👥 Lab Members")

    try:
        response = requests.get(f"{API_BASE_URL}/users")
        if response.status_code == 200:
            users = response.json()

            if users:
                # Convert to DataFrame
                df = pd.DataFrame(users)
                df = df[['id', 'name', 'email', 'github_username', 'role', 'is_active']]

                st.dataframe(df, use_container_width=True, hide_index=True)
                st.success(f"Total: {len(users)} members")
            else:
                st.info("No users yet. Add your first lab member!")
        else:
            st.error(f"Failed to load users: {response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Make sure backend is running on port 8000.")

# Page: Add User
elif page == "➕ Add User":
    st.header("➕ Add New Lab Member")

    with st.form("add_user_form"):
        name = st.text_input("Name *", placeholder="김철수")
        email = st.text_input("Email *", placeholder="student@lab.com")
        github_username = st.text_input("GitHub Username", placeholder="student_github")
        repo_url = st.text_input("Repository URL", placeholder="https://github.com/lab/student-repo")
        role = st.selectbox("Role", ["student", "advisor", "admin"])

        submit = st.form_submit_button("Add Member")

        if submit:
            if not name or not email:
                st.error("Name and Email are required!")
            else:
                try:
                    payload = {
                        "name": name,
                        "email": email,
                        "github_username": github_username if github_username else None,
                        "repo_url": repo_url if repo_url else None,
                        "role": role
                    }

                    response = requests.post(f"{API_BASE_URL}/users", json=payload)

                    if response.status_code == 201:
                        st.success(f"✅ Successfully added {name}!")
                        st.json(response.json())
                    else:
                        st.error(f"Failed: {response.json().get('detail', 'Unknown error')}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API server.")

# Page: Status
elif page == "📊 Status":
    st.header("📊 System Status")

    try:
        # API Health
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health_data = response.json()

            if health_data.get("status") == "healthy":
                st.success("✅ API Server: Healthy")
                st.success(f"✅ Database: {health_data.get('database', 'Unknown')}")
            else:
                st.error(f"❌ API Server: {health_data.get('status')}")
        else:
            st.error("❌ API Server: Unreachable")

    except:
        st.error("❌ Cannot connect to API server")

    st.markdown("---")
    st.subheader("Service URLs")
    st.code("""
    API: http://localhost:8000
    Dashboard: http://localhost:8501
    PostgreSQL: localhost:5432
    Redis: localhost:6379
    """)
