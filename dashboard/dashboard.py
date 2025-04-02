import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import streamlit as st
st.set_page_config(page_title="Quality Automation Dashboard", layout="wide")


# --- User credentials and roles ---
users = {
    "admin": {"password": "admin123", "role": "Admin"},
    "analyst": {"password": "analyst123", "role": "Analyst"},
    "support": {"password": "support123", "role": "Support"}
}

# --- Initialize session ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user = None

# --- Login Form ---
if not st.session_state.logged_in:
    st.title("🔒 Login to View Dashboard")

    st.markdown("""
    <p style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
        <strong>Available users:</strong><br>
        <code>admin / admin123</code><br>
        <code>analyst / analyst123</code><br>
        <code>support / support123</code>
    </p>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.session_state.user = username
            st.success(f"Welcome, {username} ({st.session_state.role})")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()  # Stop here if not logged in

# --- Logout ---
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Add parent directory to path to import from workflow
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from workflow.logger import Logger

# Initialize logger
logger = Logger(log_dir='../automation_logs')

# Database connection
@st.cache_resource
def get_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "tickets.db")
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_data():
    conn = get_connection()
    query = "SELECT * FROM tickets"
    df = pd.read_sql_query(query, conn)
    
    # Convert datetime strings to datetime objects
    df['created_at'] = pd.to_datetime(df['created_at'], format='ISO8601', errors='coerce')
    df['updated_at'] = pd.to_datetime(df['updated_at'], format='ISO8601', errors='coerce')
    
    return df

# Page configuration

# Title and description
st.title("Quality Automation and Operational Dashboard")
st.markdown("""
This dashboard provides real-time insights into the ticket management system.
Monitor ticket volume, priority distribution, analyst workload, and more.
""")

# Load data
df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

# Status filter
status_options = ['All'] + sorted(df['status'].unique().tolist())
selected_status = st.sidebar.multiselect(
    "Status",
    options=status_options,
    default=['All']
)

# Priority filter
priority_options = ['All'] + sorted(df['priority'].unique().tolist())
selected_priority = st.sidebar.multiselect(
    "Priority",
    options=priority_options,
    default=['All']
)

# Date range filter
min_date = df['created_at'].min().date()
max_date = df['created_at'].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(max_date - timedelta(days=14), max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    # Add a day to end_date to include the end date in the filter
    end_date = end_date + timedelta(days=1)
else:
    start_date = min_date
    end_date = max_date + timedelta(days=1)

# Apply filters
filtered_df = df.copy()

if 'All' not in selected_status:
    filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]

if 'All' not in selected_priority:
    filtered_df = filtered_df[filtered_df['priority'].isin(selected_priority)]

filtered_df = filtered_df[
    (filtered_df['created_at'] >= pd.Timestamp(start_date)) & 
    (filtered_df['created_at'] <= pd.Timestamp(end_date))
]

# Dashboard layout
col1, col2 = st.columns(2)

# Ticket Volume Overview
with col1:
    st.subheader("Ticket Volume Overview")
    
    # Bar chart of ticket counts by status
    status_counts = filtered_df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    fig_status = px.bar(
        status_counts, 
        x='Status', 
        y='Count',
        color='Status',
        title='Ticket Counts by Status',
        color_discrete_map={
            'open': '#FF9800',
            'in_progress': '#2196F3',
            'closed': '#4CAF50'
        }
    )
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Line chart of tickets created per day (last 14 days)
    daily_counts = filtered_df.groupby(filtered_df['created_at'].dt.date).size().reset_index()
    daily_counts.columns = ['Date', 'Count']
    
    fig_daily = px.line(
        daily_counts, 
        x='Date', 
        y='Count',
        title='Tickets Created per Day',
        markers=True
    )
    st.plotly_chart(fig_daily, use_container_width=True)

# Priority Breakdown
with col2:
    st.subheader("Priority Breakdown")
    
    # Pie chart: % of tickets in each priority
    priority_counts = filtered_df['priority'].value_counts().reset_index()
    priority_counts.columns = ['Priority', 'Count']
    
    fig_priority = px.pie(
        priority_counts, 
        values='Count', 
        names='Priority',
        title='Tickets by Priority',
        color='Priority',
        color_discrete_map={
            'low': '#4CAF50',
            'medium': '#FF9800',
            'high': '#F44336'
        }
    )
    st.plotly_chart(fig_priority, use_container_width=True)
    
    # Analyst Load
    st.subheader("Analyst Load")
    
    # Table: number of tickets per assigned_to
    analyst_load = filtered_df.groupby('assigned_to').size().reset_index()
    analyst_load.columns = ['Assigned To', 'Ticket Count']
    analyst_load = analyst_load.sort_values('Ticket Count', ascending=False)
    
    # Replace None with "Unassigned"
    analyst_load['Assigned To'] = analyst_load['Assigned To'].fillna('Unassigned')
    
    fig_analyst = px.bar(
        analyst_load,
        x='Assigned To',
        y='Ticket Count',
        title='Tickets per Assignee',
        color='Ticket Count',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_analyst, use_container_width=True)

# Live Feed
st.subheader("Live Feed")
st.markdown("Latest 10 tickets in the system")

# Table: last 10 tickets (with title, status, priority)
latest_tickets = filtered_df.sort_values('created_at', ascending=False).head(10)
latest_tickets_display = latest_tickets[['id', 'title', 'status', 'priority', 'assigned_to', 'created_at']]
latest_tickets_display = latest_tickets_display.rename(columns={
    'id': 'ID',
    'title': 'Title',
    'status': 'Status',
    'priority': 'Priority',
    'assigned_to': 'Assigned To',
    'created_at': 'Created At'
})

# Format the datetime for display
latest_tickets_display['Created At'] = latest_tickets_display['Created At'].dt.strftime('%Y-%m-%d %H:%M')

# Replace None with "Unassigned"
latest_tickets_display['Assigned To'] = latest_tickets_display['Assigned To'].fillna('Unassigned')

st.dataframe(latest_tickets_display, use_container_width=True)

# System Statistics
st.subheader("System Statistics")

col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

with col_stats1:
    total_tickets = len(filtered_df)
    st.metric("Total Tickets", total_tickets)

with col_stats2:
    open_tickets = len(filtered_df[filtered_df['status'] == 'open'])
    st.metric("Open Tickets", open_tickets)

with col_stats3:
    avg_resolution_time = "N/A"
    closed_tickets = filtered_df[filtered_df['status'] == 'closed']
    
    if not closed_tickets.empty:
        resolution_times = (closed_tickets['updated_at'] - closed_tickets['created_at']).dt.total_seconds() / 3600  # in hours
        avg_resolution_time = f"{resolution_times.mean():.1f} hours"
    
    st.metric("Avg. Resolution Time", avg_resolution_time)

with col_stats4:
    high_priority_count = len(filtered_df[filtered_df['priority'] == 'high'])
    high_priority_pct = (high_priority_count / total_tickets * 100) if total_tickets > 0 else 0
    st.metric("High Priority", f"{high_priority_count} ({high_priority_pct:.1f}%)")

# Footer
st.markdown("---")
st.markdown("Quality Automation Dashboard | Created for demonstration purposes")

# Log dashboard access
logger.info(f"Dashboard accessed with filters: Status={selected_status}, Priority={selected_priority}, Date Range={start_date} to {end_date}")
