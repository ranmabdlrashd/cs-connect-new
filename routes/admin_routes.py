from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models.issue import Issue
from models.request import Request
from models.notification import Notification

admin_bp = Blueprint("admin_bp", __name__)


def admin_required():
    return session.get("role") == "admin"


@admin_bp.route("/admin/library")
def admin_library():
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for("login"))

    # Get all issues and requests to display in admin dashboard (Active)
    issues = Issue.get_all_active_issues()
    requests = Request.get_all_pending_requests()

    # Unified Circulation History
    all_issues = Issue.get_all_issues()
    all_reqs = Request.get_all_requests()

    transactions = []
    for issue in all_issues:
        transactions.append({
            'type': issue['status'],  # 'issued' or 'returned'
            'book_title': issue['book_title'],
            'book_id': issue['book_id'],
            'user_name': issue['user_name'],
            'date': issue['return_date'] if issue['status'] == 'returned' and issue['return_date'] else issue['issue_date'],
            'badge_class': 'success' if issue['status'] == 'returned' else 'warning'
        })
    for req in all_reqs:
        transactions.append({
            'type': 'requested' if req['status'] == 'pending' else 'processed request',
            'book_title': req['book_title'],
            'book_id': req['book_id'],
            'user_name': req['user_name'],
            'date': req['request_date'],
            'badge_class': 'info' if req['status'] == 'pending' else 'secondary'
        })
    
    # Sort history descending
    transactions.sort(key=lambda x: str(x['date'] or ''), reverse=True)

    return render_template(
        "admin_library_dashboard.html",
        active_page="admin_dashboard",
        issues=issues,
        requests=requests,
        transactions=transactions,
    )


@admin_bp.route("/admin/notifications")
def admin_notifications():
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for("login"))

    notifications = Notification.get_admin_notifications()
    return render_template(
        "admin_notifications.html",
        active_page="admin_dashboard",
        notifications=notifications,
    )


@admin_bp.route("/admin/send_request_message/<int:request_id>", methods=["POST"])
def send_request_message(request_id):
    if not admin_required():
        return redirect(url_for("login"))

    # Find the current holder of the book
    req = Request.get_by_id(request_id)
    if req:
        book_id = req["book_id"]
        holder_id = Issue.get_current_holder_id(book_id)

        if holder_id:
            msg = "Another student has requested this book. Please return it soon."
            Notification.notify_user(holder_id, msg)

            # Optionally mark the request as processed
            Request.mark_processed(request_id)
            flash("Message sent to the current holder.", "success")
        else:
            flash("This book is not currently issued.", "warning")

    return redirect(request.referrer or url_for("admin_bp.admin_library"))
