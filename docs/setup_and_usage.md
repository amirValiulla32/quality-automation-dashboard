# Setup and Usage Instructions

This document provides detailed instructions for setting up and using the Quality Automation and Operational Dashboard Tool.

## Prerequisites

- Python 3.10 or higher
- Git (for cloning the repository)
- pip (Python package manager)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/quality-automation-dashboard.git
cd quality-automation-dashboard
```

### 2. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

If you don't have a requirements.txt file, install the dependencies manually:

```bash
pip install faker flask streamlit pandas plotly unittest
```

## Component Setup

### 1. Database Setup

Initialize the SQLite database with mock data:

```bash
cd database
python db_setup.py
```

This will:
- Create a new SQLite database file (`tickets.db`)
- Define the tickets table schema
- Generate 100 mock tickets using Faker
- Display sample data to confirm successful setup

### 2. Workflow Automation

Start the Flask application for workflow automation:

```bash
cd workflow
python app.py
```

The Flask application will run on http://localhost:5000 by default.

Available login credentials:
- Admin: username `admin`, password `admin123`
- Analyst: username `analyst`, password `analyst123`
- Support: username `support`, password `support123`

### 3. Regression Tests

Run the test suite to validate system functionality:

```bash
cd tests
python test_tickets.py
```

If any tests fail, you can fix data issues with:

```bash
python fix_outdated_tickets.py
```

### 4. Streamlit Dashboard

Launch the Streamlit dashboard:

```bash
cd dashboard
streamlit run dashboard.py
```

The dashboard will be available at http://localhost:8501

## Usage Guide

### Workflow Automation

#### API Endpoints

The Flask application provides the following API endpoints:

1. **List all tickets**
   - Method: GET
   - URL: `/api/tickets`
   - Authentication: Required (session cookie)
   - Response: JSON array of ticket objects

2. **Get a specific ticket**
   - Method: GET
   - URL: `/api/tickets/{id}`
   - Authentication: Required (session cookie)
   - Response: JSON ticket object

3. **Create a new ticket**
   - Method: POST
   - URL: `/api/tickets`
   - Authentication: Required (session cookie)
   - Request Body: JSON with ticket details
   - Required fields: `title`, `description`, `priority`
   - Response: JSON ticket object with ID

4. **Update a ticket**
   - Method: PUT
   - URL: `/api/tickets/{id}`
   - Authentication: Required (session cookie)
   - Request Body: JSON with fields to update
   - Response: JSON ticket object

5. **Webhook for external ticket creation**
   - Method: POST
   - URL: `/webhook/ticket`
   - Authentication: None (public endpoint)
   - Request Body: JSON with ticket details
   - Required fields: `title`, `description`
   - Response: JSON ticket object with ID

#### Example API Usage

Creating a new ticket:

```bash
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -b "session=your_session_cookie" \
  -d '{
    "title": "System outage in production",
    "description": "The payment processing system is down in production environment",
    "priority": "high"
  }'
```

Using the webhook endpoint:

```bash
curl -X POST http://localhost:5000/webhook/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "title": "External system alert",
    "description": "Monitoring system detected high CPU usage",
    "priority": "medium"
  }'
```

### Streamlit Dashboard

The dashboard provides several interactive components:

1. **Filters** (Sidebar)
   - Status filter: Select one or more status values
   - Priority filter: Select one or more priority values
   - Date range filter: Select start and end dates

2. **Ticket Volume Overview**
   - Bar chart showing ticket counts by status
   - Line chart showing tickets created per day

3. **Priority Breakdown**
   - Pie chart showing distribution of tickets by priority

4. **Analyst Load**
   - Bar chart showing number of tickets assigned to each analyst

5. **Live Feed**
   - Table showing the 10 most recent tickets

6. **System Statistics**
   - Total tickets
   - Open tickets
   - Average resolution time
   - High priority ticket percentage

## Automation Rules

The system implements the following automation rules:

1. **High Priority Tickets**
   - Automatically assigned to "Senior Analyst"
   - Status set to "in_progress"

2. **Low Priority Tickets**
   - Automatically assigned to "SupportBot"

3. **Priority Escalation**
   - When a low priority ticket is changed to "in_progress", it must be assigned to an analyst
   - If no analyst is specified, it defaults to "Junior Analyst"

4. **Status Integrity**
   - Closed tickets must have been updated within the last 30 days

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure the database file exists at `database/tickets.db`
   - Check file permissions
   - Run `python database/db_setup.py` to recreate the database

2. **Flask Application Not Starting**
   - Check if port 5000 is already in use
   - Ensure all dependencies are installed
   - Check for syntax errors in the code

3. **Streamlit Dashboard Not Loading**
   - Verify that Streamlit is installed correctly
   - Check if port 8501 is already in use
   - Ensure the database is accessible

4. **Test Failures**
   - Run `python tests/fix_outdated_tickets.py` to fix data integrity issues
   - Check the test logs in `test_logs/` directory for details

### Logs

- Workflow automation logs: `automation_logs/`
- Test logs: `test_logs/`

## Deployment

### Streamlit Cloud Deployment

To deploy the dashboard to Streamlit Cloud:

1. Push your code to GitHub
2. Sign up for a Streamlit Cloud account
3. Connect your GitHub repository
4. Select the `dashboard/dashboard.py` file as the main file
5. Configure any required secrets
6. Deploy the application

### Local Production Setup

For a more robust local setup:

1. Use a production WSGI server for Flask:
   ```bash
   pip install gunicorn
   cd workflow
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. Consider using a more robust database like PostgreSQL for production use.
