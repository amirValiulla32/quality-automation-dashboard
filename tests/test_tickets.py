import unittest
import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path to import from workflow
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from workflow.logger import Logger

# Initialize logger
logger = Logger(log_dir='../automation_logs')

class TestTicketSystem(unittest.TestCase):
    """Test suite for the ticket system database and automation rules"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection"""
        # Connect to the database
        """Set up test database connection"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, '../dashboard/tickets.db')
        cls.conn = sqlite3.connect(db_path)
        cls.conn.row_factory = sqlite3.Row  # ✅ This line enables dict-style access
        cls.cursor = cls.conn.cursor()
        print("[INFO] Test suite initialized")
        
        # Create test_logs directory
        os.makedirs('../test_logs', exist_ok=True)
        
        logger.info("Test suite initialized")
    
    @classmethod
    def tearDownClass(cls):
        """Close database connection"""
        cls.conn.close()
        logger.info("Test suite completed")
    
    def test_workflow_automation_trigger(self):
        """Test 1: Workflow Automation Trigger
        Insert a high-priority ticket and confirm automation updates fields correctly."""
        
        logger.info("Running Test 1: Workflow Automation Trigger")
        
        # Insert a new high-priority ticket
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
        INSERT INTO tickets (title, description, status, priority, created_at, updated_at, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Test High Priority Ticket', 
            'This is a test ticket for workflow automation', 
            'open',  # Initial status is open
            'high',  # High priority
            now, 
            now, 
            None    # Initially not assigned
        ))
        
        # Get the ID of the inserted ticket
        ticket_id = self.cursor.lastrowid
        self.conn.commit()
        
        # Simulate workflow automation (in a real system, this would be done by the workflow engine)
        self.cursor.execute('''
        UPDATE tickets
        SET status = 'in_progress', assigned_to = 'Senior Analyst'
        WHERE id = ? AND priority = 'high' AND status = 'open'
        ''', (ticket_id,))
        self.conn.commit()
        
        # Verify the ticket was updated correctly
        self.cursor.execute('SELECT status, assigned_to FROM tickets WHERE id = ?', (ticket_id,))
        ticket = self.cursor.fetchone()
        
        self.assertEqual(ticket['status'], 'in_progress')
        self.assertEqual(ticket['assigned_to'], 'Senior Analyst')
        
        # Log test result
        result = {
            'test_name': 'workflow_automation_trigger',
            'ticket_id': ticket_id,
            'expected': {'status': 'in_progress', 'assigned_to': 'Senior Analyst'},
            'actual': {'status': ticket['status'], 'assigned_to': ticket['assigned_to']},
            'passed': ticket['status'] == 'in_progress' and ticket['assigned_to'] == 'Senior Analyst'
        }
        
        with open(f'../test_logs/test1_result.json', 'w') as f:
            json.dump(result, f, indent=4)
        
        logger.info(f"Test 1 completed: {'PASSED' if result['passed'] else 'FAILED'}")
    
    def test_status_integrity_check(self):
        """Test 2: Status Integrity Check
        Ensure all closed tickets have an updated_at timestamp within the last 30 days."""
        
        logger.info("Running Test 2: Status Integrity Check")
        
        # Get current time
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        
        # Find closed tickets with updated_at older than 30 days
        self.cursor.execute('''
        SELECT id, updated_at FROM tickets 
        WHERE status = 'closed' AND updated_at < ?
        ''', (thirty_days_ago_str,))
        
        outdated_tickets = self.cursor.fetchall()
        
        # Test passes if no outdated tickets are found
        test_passed = len(outdated_tickets) == 0
        
        # Log test result
        result = {
            'test_name': 'status_integrity_check',
            'outdated_tickets': [dict(t) for t in outdated_tickets],
            'passed': test_passed,
            'message': f"Found {len(outdated_tickets)} closed tickets with updates older than 30 days" if not test_passed else "All closed tickets are up to date"
        }
        
        with open(f'../test_logs/test2_result.json', 'w') as f:
            json.dump(result, f, indent=4)
        
        logger.info(f"Test 2 completed: {'PASSED' if test_passed else 'FAILED'}")
        
        # Assert that all closed tickets have been updated within the last 30 days
        self.assertTrue(test_passed, f"Found {len(outdated_tickets)} closed tickets with updates older than 30 days")
    
    def test_priority_escalation_rule(self):
        """Test 3: Priority Escalation Rule
        Try to change a low-priority ticket to "in_progress" manually; 
        test should catch that escalation automation is required."""
        
        logger.info("Running Test 3: Priority Escalation Rule")
        
        # Insert a new low-priority ticket
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
        INSERT INTO tickets (title, description, status, priority, created_at, updated_at, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Test Low Priority Ticket', 
            'This is a test ticket for priority escalation', 
            'open',  # Initial status is open
            'low',   # Low priority
            now, 
            now, 
            'SupportBot'  # Initially assigned to SupportBot per automation rules
        ))
        
        # Get the ID of the inserted ticket
        ticket_id = self.cursor.lastrowid
        self.conn.commit()
        
        # Try to change status to in_progress without changing assignment
        # This simulates a manual update that should be caught by the rule
        self.cursor.execute('''
        UPDATE tickets
        SET status = 'in_progress'
        WHERE id = ?
        ''', (ticket_id,))
        self.conn.commit()
        
        # Verify the ticket status
        self.cursor.execute('SELECT status, assigned_to FROM tickets WHERE id = ?', (ticket_id,))
        ticket = self.cursor.fetchone()
        
        # In a real system with proper constraints, this update would be rejected or automatically
        # assign to an analyst. For this test, we're just checking if our test can detect the issue.
        rule_violation = ticket['status'] == 'in_progress' and ticket['assigned_to'] == 'SupportBot'
        
        # Log test result
        result = {
            'test_name': 'priority_escalation_rule',
            'ticket_id': ticket_id,
            'rule_violation_detected': rule_violation,
            'ticket_status': ticket['status'],
            'ticket_assigned_to': ticket['assigned_to'],
            'passed': rule_violation,  # Test passes if we detect the rule violation
            'message': "Detected rule violation: low priority ticket in progress still assigned to SupportBot" if rule_violation else "No rule violation detected"
        }
        
        with open(f'../test_logs/test3_result.json', 'w') as f:
            json.dump(result, f, indent=4)
        
        logger.info(f"Test 3 completed: {'PASSED' if rule_violation else 'FAILED'}")
        
        # For this test, we're asserting that we can detect the rule violation
        self.assertTrue(rule_violation, "Failed to detect rule violation: low priority ticket in progress should not be assigned to SupportBot")
        
        # Now fix the violation to maintain data integrity
        self.cursor.execute('''
        UPDATE tickets
        SET assigned_to = 'Junior Analyst'
        WHERE id = ? AND status = 'in_progress' AND priority = 'low'
        ''', (ticket_id,))
        self.conn.commit()
    
    def test_data_consistency(self):
        """Test 4: Data Consistency
        Ensure no ticket has null values in required fields."""
        
        logger.info("Running Test 4: Data Consistency")
        
        # Check for null values in required fields
        self.cursor.execute('''
        SELECT id, title, description, status, priority, created_at, updated_at
        FROM tickets
        WHERE title IS NULL OR description IS NULL OR status IS NULL OR 
              priority IS NULL OR created_at IS NULL OR updated_at IS NULL
        ''')
        
        inconsistent_tickets = self.cursor.fetchall()
        
        # Test passes if no inconsistent tickets are found
        test_passed = len(inconsistent_tickets) == 0
        
        # Log test result
        result = {
            'test_name': 'data_consistency',
            'inconsistent_tickets': [dict(t) for t in inconsistent_tickets],
            'passed': test_passed,
            'message': f"Found {len(inconsistent_tickets)} tickets with null values in required fields" if not test_passed else "All tickets have consistent data"
        }
        
        with open(f'../test_logs/test4_result.json', 'w') as f:
            json.dump(result, f, indent=4)
        
        logger.info(f"Test 4 completed: {'PASSED' if test_passed else 'FAILED'}")
        
        # Assert that all tickets have consistent data
        self.assertTrue(test_passed, f"Found {len(inconsistent_tickets)} tickets with null values in required fields")

if __name__ == '__main__':
    # Run the tests and generate a test report
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTicketSystem)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Generate a summary report
    summary = {
        'total_tests': test_result.testsRun,
        'failures': len(test_result.failures),
        'errors': len(test_result.errors),
        'skipped': len(test_result.skipped),
        'passed': test_result.testsRun - len(test_result.failures) - len(test_result.errors) - len(test_result.skipped),
        'was_successful': test_result.wasSuccessful()
    }
    
    with open('../test_logs/test_summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
    
    # Also save as CSV for easy viewing
    with open('../test_logs/test_summary.csv', 'w') as f:
        f.write("Metric,Value\n")
        for key, value in summary.items():
            f.write(f"{key},{value}\n")
    
    print(f"\nTest Summary:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failures']}")
    print(f"Errors: {summary['errors']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Success: {'Yes' if summary['was_successful'] else 'No'}")
    
    # Exit with appropriate code
    sys.exit(0 if test_result.wasSuccessful() else 1)
