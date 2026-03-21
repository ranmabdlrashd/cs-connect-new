import os
from dotenv import load_dotenv

# We need to make sure we're in the app context or just use get_db_connection directly.
from app import get_db_connection

books_data = [
    (
        "General Aptitude GATE/IAS/PSUs",
        "Faculty of Vani Institute, Hyderabad",
        "Vani Institute",
        "2017",
    ),
    (
        "Computer Networks",
        "Andrew S. Tanenbaum; David J. Wetherall",
        "Pearson Education Inc.",
        "2011",
    ),
    (
        "Design Thinking",
        "Rishabh Anand",
        "New Age International (P) Ltd",
        "First edition 2026",
    ),
    ("Programming in C", "Dr. S. Jose", "Pentagon Educational Services", "2019"),
    (
        "Object Oriented Programming using C++ and Java",
        "E. Balaguruswamy",
        "McGraw Hill Education",
        "5th reprint 2017",
    ),
    (
        "Web Technology & Design",
        "C. Xavier",
        "New Age International Ltd",
        "3rd Edition 2024",
    ),
    (
        "Object Oriented Programming Paradigm with Java",
        "Xavier; Chelladurai",
        "New Age International Ltd",
        "1st Edition 2025",
    ),
    (
        "Professional Ethics",
        "Dr. Sindhu R Babu ;Dr.Nizer Hussain M ;Dr. Harundrakumar V R",
        "Owl Books",
        "2021",
    ),
    (
        "Mobile Computing",
        "B.S. Charulatha",
        "Charulatha Publications",
        "Revised Edition July 2009",
    ),
    (
        "Data Communication and Networking 5E",
        "Behrouz A. Forouzan",
        "McGraw Hill Education Pvt Ltd",
        "2013",
    ),
    (
        "Software Engineering",
        "K.K. Aggarwal; Yogesh Singh",
        "New Age International (P) Ltd",
        "4th Edition 2023",
    ),
    (
        "On the Trail of Institution Builder",
        "Honour of Prof. Dr. Babu T Jose ; Rev.Dr.Clement Velluranery ; Prof. Benny Mathew Abraham ; Prof.Anitha G Pillai",
        "AISAT Publications",
        "First published Oct 2013",
    ),
    (
        "Computer System Architecture",
        "M. Morris Mano",
        "Dorling Kindersley Pvt Ltd",
        "3rd Edition 2013",
    ),
    (
        "The Architecture of Computer Hardware, System Softwar",
        "Irr Englander ;Wilson Wong",
        "Wiley India Pvt Ltd",
        "2025",
    ),
    (
        "Programming in C",
        "Dr. S. Jose",
        "Pentagonal Educational Services",
        "1st Edition 2019",
    ),
    (
        "Programming in C",
        "Dr. S. Jose",
        "Pentagonal Educational Services",
        "1st Edition 2019",
    ),
    (
        "Ultimate Placement Guide -Govt & Private Jobs",
        "K. Ganapathy Sivasubramanian; Vigneshwar Kumar",
        "Veranda Press",
        "2023",
    ),
    (
        "Programming in C",
        "Ashok N. Kamthane",
        "Dorling Kindersley Pvt Ltd",
        "2nd Edition 2011",
    ),
    (
        "Linear Algebra and Calculus",
        "Dr. Rajesh Kumar T.J; Prof. G. Aravindakshan",
        "Phasor Books",
        "2019",
    ),
    (
        "Advanced Microprocessors and Peripherals",
        "K.M. Bhurchandi; A.K. Ray",
        "McGraw Hill Education Pvt Ltd",
        "3rd Edition 2017",
    ),
    (
        "Software Engineering and Project Management",
        "R. Ruhin Kouser",
        "Lakshmi Publications",
        "1st Edition Dec 2017",
    ),
]


def import_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Delete existing books and relate tables to start fresh
    print("Clearing existing books and issues/requests...")
    cur.execute("TRUNCATE TABLE issues CASCADE")
    cur.execute("TRUNCATE TABLE requests CASCADE")
    # Resetting books table id sequence as well
    cur.execute("TRUNCATE TABLE books RESTART IDENTITY CASCADE")

    # 2. Insert new books
    print("Inserting new books...")
    for idx, (title, author, publisher, year) in enumerate(books_data):
        acc_no = idx + 1
        shelf_str = f"ACC-{acc_no}"
        desc = f"Publisher: {publisher}, Edition & Year: {year}"

        cur.execute(
            """
            INSERT INTO books (
                title, author, category, status, shelf, 
                cover_gradient, cover_icon, subject, description, 
                shelf_location, availability
            ) VALUES (
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, 
                %s, %s
            )
        """,
            (
                title,
                author,
                "textbook",  # default category
                "available",  # default status
                shelf_str,
                "linear-gradient(135deg, #667eea, #764ba2)",  # default gradient
                "fas fa-book",  # default icon
                "Computer Science",  # default subject
                desc,
                shelf_str,  # shelf_location
                True,  # availability
            ),
        )

    conn.commit()
    conn.close()
    print("Success! Inserted 21 books from spreadsheet image.")


if __name__ == "__main__":
    import_data()
