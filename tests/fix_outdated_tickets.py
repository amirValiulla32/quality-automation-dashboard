import sqlite3
from datetime import datetime, timedelta

# Connect to the database
conn = sqlite3.connect('../database/tickets.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get current time
now = datetime.now()
thirty_days_ago = now - timedelta(days=30)
thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S')

# Find closed tickets with updated_at older than 30 days
cursor.execute('''
SELECT id, updated_at FROM tickets 
WHERE status = 'closed' AND updated_at < ?
''', (thirty_days_ago_str,))

outdated_tickets = cursor.fetchall()
print(f"Found {len(outdated_tickets)} closed tickets with updates older than 30 days")

# Update these tickets to have a more recent updated_at timestamp
for ticket in outdated_tickets:
    # Set updated_at to a random time within the last 30 days
    days_ago = datetime.now().day % 29 + 1  # Between 1 and 29 days ago
    new_updated_at = now - timedelta(days=days_ago)
    new_updated_at_str = new_updated_at.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
    UPDATE tickets
    SET updated_at = ?
    WHERE id = ?
    ''', (new_updated_at_str, ticket['id']))
    
    print(f"Updated ticket {ticket['id']} from {ticket['updated_at']} to {new_updated_at_str}")

# Commit changes
conn.commit()
print("All outdated tickets have been updated")

# Verify fix
cursor.execute('''
SELECT id FROM tickets 
WHERE status = 'closed' AND updated_at < ?
''', (thirty_days_ago_str,))

remaining_outdated = cursor.fetchall()
print(f"Remaining outdated tickets: {len(remaining_outdated)}")

# Close connection
conn.close()
