import os
import sys
from datetime import datetime, timedelta

# Ensure we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from models.notification import Notification

def run_library_cron():
    """
    Cron job triggered script to monitor the issues dynamically calculated over PostgreSQL views
    and send necessary daily notifications.
    Requirements:
    - 2 days before due_date
    - On due_date
    - First day of fine (overdue start)
    - Fine increase (daily)
    """
    print(f"[{datetime.now()}] Running Library Cron Notifications...")
    
    from database import get_db_connection
    with get_db_connection() as conn:
        try:
            # Fetch all open issues where fine mapping matters
            issues = conn.execute('''
                SELECT i.sl_no, i.user_id, i.due_date, i.payment_status,
                       b.title as book_title,
                       i.days_overdue, i.fine_amount
                FROM issues_with_fines i
                JOIN books b ON i.book_id = b.sl_no
                WHERE i.status = 'issued' AND i.payment_status != 'approved'
            ''').fetchall()
            
            today = datetime.now().date()
            
            for issue in issues:
                due_date = issue['due_date'].date()
                days_until_due = (due_date - today).days
                days_overdue = issue['days_overdue']
                fine = issue['fine_amount']
                
                # Notification checks
                if days_until_due == 2:
                    Notification.notify_user(issue['user_id'], f"Reminder: '{issue['book_title']}' is due in 2 days ({due_date}).", "Library")
                
                elif days_until_due == 0:
                    Notification.notify_user(issue['user_id'], f"Action Required: '{issue['book_title']}' is due today!", "Library")
                
                elif days_until_due < 0 and issue['payment_status'] != 'pending':
                    # It is overdue. Check if it's the exact first day
                    if days_overdue == 1:
                        Notification.notify_user(issue['user_id'], f"Overdue: '{issue['book_title']}' is overdue by 1 day! A fine of ₹3 has started accruing.", "Library")
                    elif days_overdue > 1:
                        # Daily fine accumulation notification, ideally limit frequency to avoid spam
                        # For demonstration, triggers daily while overdue
                        Notification.notify_user(issue['user_id'], f"Fine Increased! '{issue['book_title']}' is overdue by {days_overdue} days. Current accrued fine: ₹{fine}.", "Library")
                        
            print(f"Success. Processed {len(issues)} active unapproved loan states for notifications.")
        except Exception as e:
            print(f"Failed to process cron jobs: {e}")


if __name__ == '__main__':
    run_library_cron()
