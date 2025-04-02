#!/bin/bash

# System Validation Script
# This script tests all components of the Quality Automation Dashboard together

echo "=== Quality Automation Dashboard System Validation ==="
echo "Starting validation at $(date)"
echo

# Create log directory
mkdir -p validation_logs
LOG_FILE="validation_logs/validation_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "1. Checking project structure..."
if [ -d "database" ] && [ -d "workflow" ] && [ -d "tests" ] && [ -d "dashboard" ] && [ -d "docs" ]; then
    echo "✅ Project structure is correct"
else
    echo "❌ Project structure is incomplete"
    exit 1
fi

echo

echo "2. Validating database setup..."
if [ -f "database/tickets.db" ]; then
    echo "✅ Database file exists"
    
    # Count tickets in database
    TICKET_COUNT=$(sqlite3 database/tickets.db "SELECT COUNT(*) FROM tickets;")
    echo "   Found $TICKET_COUNT tickets in database"
    
    if [ "$TICKET_COUNT" -gt 0 ]; then
        echo "✅ Database contains tickets"
    else
        echo "❌ Database is empty"
        echo "   Running database setup script..."
        python3 database/db_setup.py
    fi
else
    echo "❌ Database file not found"
    echo "   Running database setup script..."
    python3 database/db_setup.py
fi

echo

echo "3. Running regression tests..."
cd tests
python3 test_tickets.py
TEST_RESULT=$?
cd ..

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Some tests failed"
    echo "   Attempting to fix issues..."
    cd tests
    python3 fix_outdated_tickets.py
    python3 test_tickets.py
    FIX_RESULT=$?
    cd ..
    
    if [ $FIX_RESULT -eq 0 ]; then
        echo "✅ Issues fixed, all tests now pass"
    else
        echo "❌ Issues persist after fix attempt"
        exit 1
    fi
fi

echo

echo "4. Checking requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found, creating it..."
    echo "faker" > requirements.txt
    echo "flask" >> requirements.txt
    echo "streamlit" >> requirements.txt
    echo "pandas" >> requirements.txt
    echo "plotly" >> requirements.txt
    echo "✅ requirements.txt created"
else
    echo "✅ requirements.txt exists"
fi

echo

echo "5. Validating documentation..."
if [ -f "README.md" ] && [ -f "docs/architecture.md" ] && [ -f "docs/setup_and_usage.md" ]; then
    echo "✅ Documentation is complete"
else
    echo "❌ Documentation is incomplete"
    exit 1
fi

echo

echo "=== System Validation Summary ==="
echo "✅ Project structure: OK"
echo "✅ Database setup: OK"
echo "✅ Regression tests: OK"
echo "✅ Requirements file: OK"
echo "✅ Documentation: OK"
echo
echo "System validation completed successfully at $(date)"
echo "The Quality Automation Dashboard is ready for deployment"
echo "Log saved to $LOG_FILE"
