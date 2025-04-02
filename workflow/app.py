from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from logger import Logger

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

# Initialize logger
logger = Logger()

# Mock users for login simulation
USERS = {
    'admin': {
        'password': generate_password_hash('admin123'),
        'role': 'admin'
    },
    'analyst': {
        'password': generate_password_hash('analyst123'),
        'role': 'analyst'
    },
    'support': {
        'password': generate_password_hash('support123'),
        'role': 'support'
    }
}

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('../database/tickets.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'], role=session['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and check_password_hash(USERS[username]['password'], password):
            session['username'] = username
            session['role'] = USERS[username]['role']
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
        
        logger.warning(f"Failed login attempt for user {username}")
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.pop('username', None)
    session.pop('role', None)
    if username:
        logger.info(f"User {username} logged out")
    return redirect(url_for('login'))

# API endpoints
@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    
    # Convert to list of dicts
    result = [dict(ticket) for ticket in tickets]
    return jsonify(result)

@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()
    
    if ticket is None:
        return jsonify({"error": "Ticket not found"}), 404
    
    return jsonify(dict(ticket))

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    # Validate required fields
    required_fields = ['title', 'description', 'priority']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Set default values
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['status'] = 'open'
    data['created_at'] = now
    data['updated_at'] = now
    data['assigned_to'] = None
    
    # Apply automation rules
    if data['priority'] == 'high':
        data['status'] = 'in_progress'
        data['assigned_to'] = 'Senior Analyst'
        logger.info(f"High priority ticket automatically assigned to Senior Analyst")
    elif data['priority'] == 'low':
        data['assigned_to'] = 'SupportBot'
        logger.info(f"Low priority ticket automatically assigned to SupportBot")
    
    # Insert into database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO tickets (title, description, status, priority, created_at, updated_at, assigned_to)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'], 
        data['description'], 
        data['status'], 
        data['priority'], 
        data['created_at'], 
        data['updated_at'], 
        data['assigned_to']
    ))
    
    # Get the ID of the inserted ticket
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.success(f"New ticket created: ID={ticket_id}, Title={data['title']}, Priority={data['priority']}")
    
    # Return the created ticket
    return jsonify({
        "id": ticket_id,
        **data
    }), 201

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    # Get current ticket data
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    
    if ticket is None:
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404
    
    current_ticket = dict(ticket)
    
    # Apply automation rules
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['updated_at'] = now
    
    # Rule: If changing from low priority to in_progress, must be assigned to an analyst
    if (current_ticket['priority'] == 'low' and 
        data.get('status') == 'in_progress' and 
        current_ticket['status'] != 'in_progress'):
        
        if 'assigned_to' not in data or data['assigned_to'] is None:
            data['assigned_to'] = 'Junior Analyst'
            logger.info(f"Low priority ticket escalated to in_progress, automatically assigned to Junior Analyst")
    
    # Rule: High priority tickets must be assigned to Senior Analyst
    if data.get('priority') == 'high' and current_ticket['priority'] != 'high':
        data['assigned_to'] = 'Senior Analyst'
        if data.get('status') == 'open':
            data['status'] = 'in_progress'
        logger.info(f"Ticket escalated to high priority, automatically assigned to Senior Analyst")
    
    # Update fields
    fields = ['title', 'description', 'status', 'priority', 'assigned_to', 'updated_at']
    updates = []
    values = []
    
    for field in fields:
        if field in data:
            updates.append(f"{field} = ?")
            values.append(data[field])
    
    if not updates:
        conn.close()
        return jsonify({"error": "No fields to update"}), 400
    
    # Execute update
    values.append(ticket_id)
    cursor = conn.cursor()
    cursor.execute(f'''
    UPDATE tickets 
    SET {", ".join(updates)}
    WHERE id = ?
    ''', values)
    
    conn.commit()
    conn.close()
    
    logger.success(f"Ticket updated: ID={ticket_id}")
    
    # Return updated ticket
    return jsonify({
        "id": ticket_id,
        **{**current_ticket, **data}
    })

@app.route('/webhook/ticket', methods=['POST'])
def webhook_ticket():
    """Webhook endpoint for external systems to create tickets"""
    data = request.json
    
    # Validate webhook data
    if not data or 'title' not in data or 'description' not in data:
        logger.error("Invalid webhook data received")
        return jsonify({"error": "Invalid data"}), 400
    
    # Set default values if not provided
    if 'priority' not in data:
        data['priority'] = 'medium'
    
    # Create ticket with the same logic as the regular endpoint
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ticket_data = {
        'title': data['title'],
        'description': data['description'],
        'priority': data['priority'],
        'status': 'open',
        'created_at': now,
        'updated_at': now,
        'assigned_to': None
    }
    
    # Apply automation rules
    if ticket_data['priority'] == 'high':
        ticket_data['status'] = 'in_progress'
        ticket_data['assigned_to'] = 'Senior Analyst'
    elif ticket_data['priority'] == 'low':
        ticket_data['assigned_to'] = 'SupportBot'
    
    # Insert into database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO tickets (title, description, status, priority, created_at, updated_at, assigned_to)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        ticket_data['title'], 
        ticket_data['description'], 
        ticket_data['status'], 
        ticket_data['priority'], 
        ticket_data['created_at'], 
        ticket_data['updated_at'], 
        ticket_data['assigned_to']
    ))
    
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.success(f"New ticket created via webhook: ID={ticket_id}, Title={ticket_data['title']}")
    
    return jsonify({
        "id": ticket_id,
        "message": "Ticket created successfully",
        **ticket_data
    }), 201

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Create simple templates if they don't exist
    if not os.path.exists('templates/login.html'):
        with open('templates/login.html', 'w') as f:
            f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Quality Automation Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f5f5f5; }
        .login-container { background: white; padding: 2rem; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 350px; }
        h1 { text-align: center; color: #333; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
        input[type="text"], input[type="password"] { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 3px; }
        button { background: #4CAF50; color: white; border: none; padding: 0.7rem 1rem; border-radius: 3px; cursor: pointer; width: 100%; }
        button:hover { background: #45a049; }
        .error { color: red; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Quality Automation Dashboard</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <p style="text-align: center; margin-top: 1rem; font-size: 0.8rem;">
            Available users: admin/admin123, analyst/analyst123, support/support123
        </p>
    </div>
</body>
</html>
            ''')
    
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Quality Automation Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background: #4CAF50; color: white; padding: 1rem; display: flex; justify-content: space-between; align-items: center; }
        .content { padding: 1rem; }
        .logout { color: white; text-decoration: none; }
        .card { background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 1rem; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Quality Automation Dashboard</h1>
        <div>
            <span>Welcome, {{ username }} ({{ role }})</span>
            <a href="/logout" class="logout">Logout</a>
        </div>
    </div>
    <div class="content">
        <div class="card">
            <h2>Welcome to the Quality Automation System</h2>
            <p>This is a simple interface for the workflow automation system. The main dashboard is implemented in Streamlit.</p>
            <p>Your role: <strong>{{ role }}</strong></p>
            <p>Available API endpoints:</p>
            <ul>
                <li><code>GET /api/tickets</code> - List all tickets</li>
                <li><code>GET /api/tickets/{id}</code> - Get a specific ticket</li>
                <li><code>POST /api/tickets</code> - Create a new ticket</li>
                <li><code>PUT /api/tickets/{id}</code> - Update a ticket</li>
                <li><code>POST /webhook/ticket</code> - External webhook for ticket creation</li>
            </ul>
            <p>For the full dashboard experience, please use the Streamlit interface.</p>
        </div>
    </div>
</body>
</html>
            ''')
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
