from datetime import datetime, timedelta
import sqlite3
import os
import random
from faker import Faker

# Ensure database directory exists
os.makedirs('database', exist_ok=True)

# Create test_logs directory
os.makedirs('test_logs', exist_ok=True)

# Initialize Faker
fake = Faker()

# Database connection
conn = sqlite3.connect('database/tickets.db')
cursor = conn.cursor()

# Create tickets table
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT CHECK(status IN ('open', 'in_progress', 'closed')) NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    assigned_to TEXT
)
''')

# Generate 100 mock tickets
print("Generating 100 mock tickets...")

# List of possible assignees
assignees = ["SupportBot", "Junior Analyst", "Senior Analyst", "Team Lead", None]
statuses = ["open", "in_progress", "closed"]
priorities = ["low", "medium", "high"]

# Current time
now = datetime.now()

# Insert mock data
for i in range(1, 101):
    # Generate random dates within the last 60 days
    created_days_ago = fake.random_int(min=0, max=60)
    created_at = now - timedelta(days=created_days_ago)
    
    # Updated date is after created date
    updated_days_ago = fake.random_int(min=0, max=created_days_ago)
    updated_at = now - timedelta(days=updated_days_ago)
    
    # Generate random status
    status_choices = ['open', 'in_progress', 'closed']
    status_weights = [0.3, 0.3, 0.4]
    status = random.choices(status_choices, weights=status_weights, k=1)[0]
    
    # Generate random priority
    priority_choices = ['low', 'medium', 'high']
    priority_weights = [0.5, 0.3, 0.2]
    priority = random.choices(priority_choices, weights=priority_weights, k=1)[0]
    
    # Assign based on status and priority
    if status == 'closed':
        assigned_to = fake.random_element(elements=["Junior Analyst", "Senior Analyst", "Team Lead"])
    elif status == 'in_progress':
        if priority == 'high':
            assigned_to = "Senior Analyst"
        else:
            assigned_to = fake.random_element(elements=["Junior Analyst", "Senior Analyst"])
    else:  # open
        if priority == 'low':
            assigned_to = "SupportBot"
        else:
            assigned_to = None  # Not assigned yet
    
    # Generate ticket data
    title = fake.sentence(nb_words=6)[:-1]  # Remove period
    description = fake.paragraph(nb_sentences=3)
    
    # Insert into database
    cursor.execute('''
    INSERT INTO tickets (title, description, status, priority, created_at, updated_at, assigned_to)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, status, priority, created_at, updated_at, assigned_to))

# Commit changes and close connection
conn.commit()
print("Database setup complete!")

# Display some sample data
cursor.execute("SELECT id, title, status, priority, assigned_to FROM tickets LIMIT 5")
sample_data = cursor.fetchall()
print("\nSample data:")
for row in sample_data:
    print(row)

conn.close()
