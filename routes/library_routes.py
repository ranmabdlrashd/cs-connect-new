from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    jsonify,
)
from models.book import Book
from models.issue import Issue
from models.request import Request
from models.notification import Notification

library_bp = Blueprint("library_bp", __name__)


@library_bp.route("/library")
def library():
    if "user_id" not in session:
        flash("Please log in to access the library.", "warning")
        return redirect(url_for("login"))
    return render_template("library.html", active_page="library")


@library_bp.route("/search_books")
def search_books():
    if "user_id" not in session:
        return jsonify([])

    query = request.args.get("q", "").strip()
    if query:
        books = Book.search(query)
    else:
        books = Book.get_all()

    # We also need to get the current holder if issued
    # We can fetch this directly or join in the model
    # For now, let's just enhance the books list with current holder info if availability is false
    results = []
    for b in books:
        holder = None
        if not b.get("availability", True):
            holder_name = Issue.get_current_holder(b["id"])
            if holder_name:
                holder = holder_name

        b["current_holder"] = holder
        results.append(b)

    return jsonify(results)


@library_bp.route("/book/<int:book_id>")
def book_details(book_id):
    if "user_id" not in session:
        flash("Please log in to view book details.", "warning")
        return redirect(url_for("login"))

    book = Book.get_by_id(book_id)
    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("library_bp.library"))

    holder = None
    if not book.get("availability", True):
        holder = Issue.get_current_holder(book_id)

    pending_requests = []
    history = []
    if session.get("role") == "admin":
        pending_requests = Request.get_pending_requests_by_book(book_id)
        history = Issue.get_history_by_book(book_id)

    return render_template(
        "book_details.html",
        book=book,
        active_page="library",
        holder=holder,
        pending_requests=pending_requests,
        history=history,
    )


@library_bp.route("/issue_book/<int:book_id>", methods=["POST"])
def issue_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        flash("Admins cannot issue books.", "danger")
        return redirect(url_for("library_bp.book_details", book_id=book_id))

    user_id = session["user_id"]
    book = Book.get_by_id(book_id)

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("library_bp.library"))

    if not book.get("availability", True):
        flash("This book is already issued.", "danger")
    elif Issue.has_user_issued_book(user_id, book_id):
        flash("You have already issued this book.", "danger")
    else:
        # Issue the book
        Issue.create_issue(book_id, user_id)
        Book.update_availability(book_id, False)

        # Notify Admin (Role based notification: here we just need a way to notify admins.
        # Usually we might leave user_id=0 for all admins, or find admin IDs.
        # For this requirement, let's assume user_id=0 means general admin notification)
        Notification.notify_admin(
            f"User {session.get('name')} issued book '{book['title']}' (ID: {book_id})."
        )

        flash("Book issued successfully.", "success")

    return redirect(url_for("library_bp.book_details", book_id=book_id))


@library_bp.route("/return_book/<int:book_id>", methods=["POST"])
def return_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        flash("Admins cannot return books.", "danger")
        return redirect(url_for("library_bp.book_details", book_id=book_id))

    user_id = session["user_id"]
    book = Book.get_by_id(book_id)

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("library_bp.library"))

    if book.get("availability", True):
        flash("This book is not currently issued.", "warning")
    elif not Issue.is_user_issuer(user_id, book_id):
        flash("You cannot return a book issued by another user.", "danger")
    else:
        # Return book
        Issue.return_book(book_id)
        Book.update_availability(book_id, True)

        Notification.notify_admin(
            f"User {session.get('name')} returned book '{book['title']}' (ID: {book_id})."
        )

        flash("Book returned successfully.", "success")

    return redirect(url_for("library_bp.book_details", book_id=book_id))


@library_bp.route("/request_book/<int:book_id>", methods=["POST"])
def request_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        flash("Admins cannot request books.", "danger")
        return redirect(url_for("library_bp.book_details", book_id=book_id))

    user_id = session["user_id"]
    book = Book.get_by_id(book_id)

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("library_bp.library"))

    if book.get("availability", True):
        flash("This book is already available. You can issue it.", "info")
    else:
        # Request book
        Request.create_request(book_id, user_id)

        # Notify admin of the request
        Notification.notify_admin(
            f"User {session.get('name')} requested to reserve book '{book['title']}' (ID: {book_id})."
        )
        
        # Check if book is currently issued, and notify the current issuer
        from models.issue import Issue
        is_avail = book.get("availability", True)
        # Using string check as well just in case
        if is_avail is False or is_avail == 'False' or is_avail == 0:
            holder_id = Issue.get_current_holder_id(book_id)
            if holder_id:
                Notification.notify_user(
                    holder_id,
                    f"Warning: Another user has requested the book '{book['title']}' which is currently issued to you. Please return it as soon as possible."
                )

        flash("Book request sent to admin.", "success")

    return redirect(url_for("library_bp.book_details", book_id=book_id))
