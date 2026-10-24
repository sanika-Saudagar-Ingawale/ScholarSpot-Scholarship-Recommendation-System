from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, Response
import csv
import io
from pathlib import Path
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import IntegrityError

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-this-with-a-long-random-secret-before-deployment"

# Set these to match your local MySQL Workbench connection.
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Kitty$818",
    "database": "scholarship_db",
    "port": 3306,
    "charset": "utf8mb4",
    "use_unicode": True,
}


class MySQLDB:
    """Small compatibility wrapper so routes can keep using db.execute(...)."""

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def _sql(query):
        # The original SQLite code uses ? placeholders. MySQL Connector uses %s.
        return query.replace("?", "%s")

    def execute(self, query, params=None):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(self._sql(query), params or ())
        return cursor

    def executemany(self, query, params):
        cursor = self.connection.cursor()
        cursor.executemany(self._sql(query), params)
        return cursor

    def executescript(self, script):
        # Kept only as a convenience; each CREATE statement is executed separately.
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                self.execute(statement)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


class DBContext:
    def __enter__(self):
        self.raw_connection = mysql.connector.connect(**MYSQL_CONFIG)
        self.db = MySQLDB(self.raw_connection)
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.raw_connection.commit()
        else:
            self.raw_connection.rollback()
        self.raw_connection.close()
        return False


def get_db():
    return DBContext()


def init_db():
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(30) NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS scholarships (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            provider VARCHAR(255) NOT NULL,
            region VARCHAR(100) NOT NULL DEFAULT 'All India',
            education VARCHAR(100) NOT NULL DEFAULT 'Bachelor''s',
            community VARCHAR(100) NOT NULL DEFAULT 'All communities',
            funding VARCHAR(100) NOT NULL DEFAULT 'Fee Support',
            award VARCHAR(255) NOT NULL,
            amount BIGINT NOT NULL DEFAULT 0,
            status VARCHAR(50) NOT NULL DEFAULT 'Open',
            deadline VARCHAR(255) NOT NULL DEFAULT 'Check official website',
            description TEXT NOT NULL,
            eligibility TEXT NOT NULL,
            documents TEXT NOT NULL,
            official_url VARCHAR(1000) NOT NULL DEFAULT 'https://scholarships.gov.in/',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_scholarships_name (name),
            INDEX idx_scholarships_region (region),
            INDEX idx_scholarships_education (education),
            INDEX idx_scholarships_community (community),
            INDEX idx_scholarships_status (status)
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS saved_scholarships (
            user_id INT NOT NULL,
            scholarship_id INT NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, scholarship_id),
            CONSTRAINT fk_saved_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT fk_saved_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            scholarship_id INT NOT NULL,
            status VARCHAR(60) NOT NULL DEFAULT 'Interested',
            notes VARCHAR(1000) NOT NULL DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_application_user_scholarship (user_id, scholarship_id),
            CONSTRAINT fk_application_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT fk_application_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS student_profiles (
            user_id INT NOT NULL PRIMARY KEY,
            course VARCHAR(150) NOT NULL DEFAULT '',
            study_year VARCHAR(50) NOT NULL DEFAULT '',
            marks VARCHAR(50) NOT NULL DEFAULT '',
            annual_income VARCHAR(100) NOT NULL DEFAULT '',
            state VARCHAR(100) NOT NULL DEFAULT '',
            category VARCHAR(100) NOT NULL DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    ]

    with get_db() as db:
        for statement in statements:
            db.execute(statement)

        count = db.execute("SELECT COUNT(*) AS total FROM scholarships").fetchone()["total"]
        if count == 0:
            demo_scholarships = [
                ("National Scholarship Portal – Scheme Directory", "Government of India", "All India", "Bachelor's", "All communities", "Fee Support", "Varies by scheme", 20000, "Open", "Check official notification", "Directory-style sample entry representing scholarships listed through the National Scholarship Portal. The actual benefits and eligibility depend on the specific scheme.", "Read the current scheme guidelines; course, marks, income, domicile or category requirements may apply.", "Aadhaar or accepted ID; student ID; marksheets; bank details; income/category certificate if required.", "https://scholarships.gov.in/"),
                ("Maharashtra MahaDBT Scholarship Schemes", "Government of Maharashtra", "Maharashtra", "Bachelor's", "SC / ST / OBC", "Fee Support", "Varies by scheme", 25000, "Open", "Check MahaDBT portal", "Sample entry for state scholarship schemes. This is not a claim that every scheme is currently accepting applications.", "Maharashtra domicile and course requirements may apply. Eligibility varies by scheme and student category.", "Domicile certificate; income certificate; marksheet; admission details; bank information; category certificate where applicable.", "https://mahadbt.maharashtra.gov.in/"),
                ("Sitaram Jindal Foundation Scholarship", "Sitaram Jindal Foundation", "All India", "Diploma", "All communities", "Monthly Stipend", "Varies by course and eligibility", 3200, "Always Open", "Verify on official website", "Demo listing for a scholarship opportunity. Check the foundation's official information for current rules and application instructions.", "Academic level, marks and family income criteria may apply. Check the current official guidelines.", "Recent marksheet; proof of admission; income proof; identity proof; other documents requested by the foundation.", "https://www.scholarshipforme.com/"),
                ("Bright Start Student Support (Demo)", "Scholar Spot Demo Provider", "Maharashtra", "Class XII", "General", "Partial Funding", "Up to ₹10,000 (demo)", 10000, "Open", "Demo date — verify before use", "Fictional demonstration scholarship used to test the website. It is not a real award and must not be used as a real application.", "Demo record only; no real eligibility rules.", "Demo only; no real application documents.", "https://scholarships.gov.in/"),
                ("Research Excellence Fellowship (Demo)", "Scholar Spot Demo Provider", "All India", "Master's", "All communities", "Monthly Stipend", "See official notification", 30000, "Closed", "Demo status", "Fictional record demonstrating the closed application status in the user interface.", "Demo record only; no real eligibility rules.", "Demo only; no real application documents.", "https://scholarships.gov.in/"),
                ("International Study Grant (Demo)", "Scholar Spot Demo Provider", "International", "Master's", "All communities", "Full Funding", "Depends on provider", 50000, "Always Open", "Depends on institution", "Fictional demonstration record for international scholarship filters.", "Check the relevant institution or provider for actual requirements.", "Usually varies by institution; this is a demo record.", "https://www.scholarshipforme.com/")
            ]
            db.executemany(
                """INSERT INTO scholarships
                (name, provider, region, education, community, funding, award, amount, status, deadline,
                 description, eligibility, documents, official_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                demo_scholarships
            )

        admin = db.execute("SELECT id FROM users WHERE email = %s", ("admin@scholarspot.in",)).fetchone()
        if not admin:
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ("Site Admin", "admin@scholarspot.in", generate_password_hash("Admin@123"), "admin")
            )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_user": {
        "id": session.get("user_id"),
        "name": session.get("user_name"),
        "role": session.get("role")
    } if session.get("user_id") else None}


@app.route("/")
def home():
    with get_db() as db:
        featured = db.execute("SELECT * FROM scholarships ORDER BY id DESC LIMIT 3").fetchall()
        total = db.execute("SELECT COUNT(*) AS total FROM scholarships").fetchone()["total"]
    return render_template("index.html", featured=featured, total=total)


@app.route("/scholarships")
def scholarships():
    q = request.args.get("q", "").strip()
    region = request.args.get("region", "").strip()
    education = request.args.get("education", "").strip()
    community = request.args.get("community", "").strip()
    funding = request.args.get("funding", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "newest")

    sql = "SELECT * FROM scholarships WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE %s OR provider LIKE %s OR description LIKE %s OR education LIKE %s)"
        term = f"%{q}%"
        params.extend([term, term, term, term])
    for column, value in [("region", region), ("education", education), ("community", community), ("funding", funding), ("status", status)]:
        if value:
            sql += f" AND {column} = %s"
            params.append(value)
    if sort == "amount":
        sql += " ORDER BY amount DESC, name ASC"
    elif sort == "name":
        sql += " ORDER BY name ASC"
    else:
        sql += " ORDER BY id DESC"

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
        saved_ids = set()
        if session.get("user_id"):
            saved_ids = {r["scholarship_id"] for r in db.execute(
                "SELECT scholarship_id FROM saved_scholarships WHERE user_id = %s",
                (session["user_id"],)
            ).fetchall()}
    return render_template("scholarships.html", scholarships=rows, saved_ids=saved_ids,
                           filters={"q": q, "region": region, "education": education,
                                    "community": community, "funding": funding, "status": status, "sort": sort})


@app.route("/scholarship/<int:scholarship_id>")
def scholarship_detail(scholarship_id):
    with get_db() as db:
        item = db.execute("SELECT * FROM scholarships WHERE id = %s", (scholarship_id,)).fetchone()
        saved = False
        if item and session.get("user_id"):
            saved = db.execute("SELECT 1 AS found FROM saved_scholarships WHERE user_id = %s AND scholarship_id = %s",
                               (session["user_id"], scholarship_id)).fetchone() is not None
    if not item:
        abort(404)
    return render_template("detail.html", item=item, saved=saved)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            try:
                with get_db() as db:
                    db.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                               (name, email, generate_password_hash(password)))
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("login"))
            except IntegrityError:
                flash("An account with that email already exists.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome, {user['name']}!", "success")
            target = request.args.get("next", "")
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("admin") if user["role"] == "admin" else url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as db:
        saved = db.execute("""SELECT s.* FROM scholarships s
            JOIN saved_scholarships ss ON ss.scholarship_id = s.id
            WHERE ss.user_id = %s ORDER BY ss.saved_at DESC""", (session["user_id"],)).fetchall()
    return render_template("dashboard.html", saved=saved)


@app.route("/save/<int:scholarship_id>", methods=["POST"])
@login_required
def save_scholarship(scholarship_id):
    with get_db() as db:
        exists = db.execute("SELECT id FROM scholarships WHERE id = %s", (scholarship_id,)).fetchone()
        if not exists:
            abort(404)
        already = db.execute("SELECT 1 AS found FROM saved_scholarships WHERE user_id = %s AND scholarship_id = %s",
                             (session["user_id"], scholarship_id)).fetchone()
        if already:
            db.execute("DELETE FROM saved_scholarships WHERE user_id = %s AND scholarship_id = %s",
                       (session["user_id"], scholarship_id))
            flash("Scholarship removed from your saved list.", "info")
        else:
            db.execute("INSERT INTO saved_scholarships (user_id, scholarship_id) VALUES (%s, %s)",
                       (session["user_id"], scholarship_id))
            flash("Scholarship saved to your dashboard.", "success")
    return redirect(request.form.get("next") or url_for("scholarship_detail", scholarship_id=scholarship_id))


@app.route("/admin", methods=["GET", "POST"])
@login_required
@admin_required
def admin():
    if request.method == "POST":
        action = request.form.get("action")
        with get_db() as db:
            if action == "delete":
                db.execute("DELETE FROM scholarships WHERE id = %s", (request.form.get("id"),))
                flash("Scholarship deleted.", "success")
            else:
                fields = ["name", "provider", "region", "education", "community", "funding", "award",
                          "amount", "status", "deadline", "description", "eligibility", "documents", "official_url"]
                values = [request.form.get(field, "").strip() for field in fields]
                try:
                    values[7] = int(values[7] or 0)
                except ValueError:
                    values[7] = 0
                if not values[0] or not values[1] or not values[6] or not values[10]:
                    flash("Name, provider, award and description are required.", "error")
                else:
                    scholarship_id = request.form.get("id")
                    if scholarship_id:
                        db.execute("""UPDATE scholarships SET name=%s, provider=%s, region=%s, education=%s, community=%s,
                            funding=%s, award=%s, amount=%s, status=%s, deadline=%s, description=%s, eligibility=%s, documents=%s,
                            official_url=%s WHERE id=%s""", values + [scholarship_id])
                        flash("Scholarship updated.", "success")
                    else:
                        db.execute("""INSERT INTO scholarships (name, provider, region, education, community, funding,
                            award, amount, status, deadline, description, eligibility, documents, official_url)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", values)
                        flash("Scholarship added.", "success")
        return redirect(url_for("admin"))
    edit_id = request.args.get("edit", type=int)
    with get_db() as db:
        rows = db.execute("SELECT * FROM scholarships ORDER BY id DESC").fetchall()
        edit_item = db.execute("SELECT * FROM scholarships WHERE id = %s", (edit_id,)).fetchone() if edit_id else None
    return render_template("admin.html", scholarships=rows, edit_item=edit_item)


@app.route("/admin/import-csv", methods=["POST"])
@login_required
@admin_required
def import_scholarships_csv():
    uploaded_file = request.files.get("csv_file")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a CSV file.", "error")
        return redirect(url_for("admin"))

    if not uploaded_file.filename.lower().endswith(".csv"):
        flash("Only CSV files are allowed.", "error")
        return redirect(url_for("admin"))

    try:
        content = uploaded_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = [
            "name", "provider", "region", "education", "community",
            "funding", "award", "amount", "status", "deadline",
            "description", "eligibility", "documents", "official_url"
        ]

        if not reader.fieldnames:
            flash("The CSV file is empty.", "error")
            return redirect(url_for("admin"))

        # Ignore accidental spaces in column names.
        reader.fieldnames = [column.strip() for column in reader.fieldnames]

        missing = set(required_columns) - set(reader.fieldnames)
        if missing:
            flash(
                "Missing CSV columns: " + ", ".join(sorted(missing)),
                "error"
            )
            return redirect(url_for("admin"))

        added = 0
        skipped = 0

        with get_db() as db:
            for row in reader:
                name = (row.get("name") or "").strip()
                provider = (row.get("provider") or "").strip()
                award = (row.get("award") or "").strip()
                description = (row.get("description") or "").strip()

                if not name or not provider or not award or not description:
                    skipped += 1
                    continue

                try:
                    amount = int((row.get("amount") or "0").strip() or 0)
                    if amount < 0:
                        skipped += 1
                        continue
                except ValueError:
                    skipped += 1
                    continue

                # Avoid importing a scholarship with the same name and provider.
                existing = db.execute(
                    """
                    SELECT id FROM scholarships
                    WHERE LOWER(name) = LOWER(%s)
                      AND LOWER(provider) = LOWER(%s)
                    LIMIT 1
                    """,
                    (name, provider)
                ).fetchone()

                if existing:
                    skipped += 1
                    continue

                db.execute(
                    """
                    INSERT INTO scholarships (
                        name, provider, region, education, community, funding,
                        award, amount, status, deadline, description, eligibility,
                        documents, official_url
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        name,
                        provider,
                        (row.get("region") or "All India").strip() or "All India",
                        (row.get("education") or "Bachelor's").strip() or "Bachelor's",
                        (row.get("community") or "All communities").strip() or "All communities",
                        (row.get("funding") or "Fee Support").strip() or "Fee Support",
                        award,
                        amount,
                        (row.get("status") or "Open").strip() or "Open",
                        (row.get("deadline") or "Check official website").strip()
                            or "Check official website",
                        description,
                        (row.get("eligibility") or "Check official eligibility criteria").strip()
                            or "Check official eligibility criteria",
                        (row.get("documents") or "Check official website").strip()
                            or "Check official website",
                        (row.get("official_url") or "https://scholarships.gov.in/").strip()
                            or "https://scholarships.gov.in/"
                    )
                )
                added += 1

        flash(
            f"CSV import completed. Added: {added}; skipped: {skipped}.",
            "success" if added else "error"
        )

    except (UnicodeDecodeError, csv.Error) as error:
        flash(f"Could not read CSV file: {error}", "error")
    except Exception as error:
        print("CSV import error:", error)
        flash("Import failed. Check the terminal for the database error.", "error")

    return redirect(url_for("admin"))







@app.route("/matched-scholarships")
@login_required
def matched_scholarships():
    user_id = session["user_id"]

    with get_db() as db:
        profile_data = db.execute(
            """
            SELECT course, study_year, marks, annual_income, state, category
            FROM student_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        ).fetchone()

        if not profile_data:
            flash("Please complete your student profile first.", "info")
            return redirect(url_for("profile"))

        scholarships = db.execute(
            """
            SELECT *
            FROM scholarships
            WHERE LOWER(status) IN ('open', 'always open')
            ORDER BY id DESC
            """
        ).fetchall()

        saved_rows = db.execute(
            """
            SELECT scholarship_id
            FROM saved_scholarships
            WHERE user_id = %s
            """,
            (user_id,)
        ).fetchall()

    def clean(value):
        return str(value or "").strip().lower()

    def number(value):
        try:
            if value is None or str(value).strip() == "":
                return None
            return float(value)
        except (ValueError, TypeError):
            return None

    course = clean(profile_data.get("course"))
    state = clean(profile_data.get("state"))
    category = clean(profile_data.get("category"))
    marks = number(profile_data.get("marks"))
    income = number(profile_data.get("annual_income"))

    def course_matches(student_course, scholarship_education):
        student_course = clean(student_course)
        education = clean(scholarship_education)

        if not student_course or not education:
            return False

        if any(word in education for word in
               ["all levels", "all courses", "all students", "all"]):
            return True

        if any(word in student_course for word in
               ["btech", "b.tech", "b.e.", "b.e ", "bachelor",
                "undergraduate", "degree", "b.sc", "bca", "bba"]):
            return any(word in education for word in
                       ["bachelor", "undergraduate", "graduation",
                        "degree", "undergraduate (ug)", "ug"])

        if "diploma" in student_course:
            return "diploma" in education

        if any(word in student_course for word in
               ["master", "mtech", "m.tech", "mba", "m.sc",
                "postgraduate"]):
            return any(word in education for word in
                       ["master", "postgraduate", "post graduate", "pg"])

        if any(word in student_course for word in
               ["12th", "class 12", "hsc", "higher secondary"]):
            return any(word in education for word in
                       ["class xii", "class 12", "12th", "hsc"])

        if any(word in student_course for word in
               ["10th", "class 10", "ssc", "secondary"]):
            return any(word in education for word in
                       ["class x", "class 10", "10th", "ssc"])

        return student_course == education

    def region_matches(student_state, scholarship_region):
        region = clean(scholarship_region)

        if any(word in region for word in
               ["all india", "india", "all states", "national"]):
            return True

        if not student_state or not region:
            return False

        return student_state == region

    def category_matches(student_category, scholarship_community):
        community = clean(scholarship_community)

        if any(word in community for word in
               ["all communities", "all categories", "all students",
                "all category", "any category", "all"]):
            return True

        if not student_category or not community:
            return False

        return (
            student_category == community
            or student_category in community
        )

    matched = []

    for scholarship in scholarships:
        reasons = []

        # Education must match.
        if not course_matches(course, scholarship.get("education")):
            continue
        reasons.append("Education level matches")

        # State or All-India eligibility must match.
        if not region_matches(state, scholarship.get("region")):
            continue
        reasons.append("Location matches")

        # Community/category must match.
        if not category_matches(category, scholarship.get("community")):
            continue
        reasons.append("Category matches")

        # Minimum marks: if specified, student marks must be available
        # and must meet the minimum.
        min_marks = number(scholarship.get("min_marks"))

        if min_marks is not None:
            if marks is None or marks < min_marks:
                continue
            reasons.append("Minimum marks requirement met")

        # Maximum family annual income: if specified, income must be
        # available and must not exceed the limit.
        max_income = number(scholarship.get("max_annual_income"))

        if max_income is not None:
            if income is None or income > max_income:
                continue
            reasons.append("Family income requirement met")

        # Score is for display/ranking only, not the eligibility decision.
        scholarship["match_score"] = min(100, len(reasons) * 20)
        scholarship["match_reasons"] = reasons
        matched.append(scholarship)

    matched.sort(
        key=lambda item: (
            item["match_score"],
            number(item.get("amount")) or 0
        ),
        reverse=True
    )

    saved_ids = {row["scholarship_id"] for row in saved_rows}

    return render_template(
        "matched_scholarships.html",
        scholarships=matched,
        saved_ids=saved_ids,
        profile_data=profile_data
    )





@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        fields = [
            "course", "study_year", "marks", "annual_income", "state",
            "category", "date_of_birth", "gender", "phone", "address",
            "city", "district", "pincode", "domicile_state", "college",
            "admission_year", "tenth_percentage", "twelfth_percentage",
            "previous_percentage", "parent_guardian_name",
            "parent_occupation", "minority_status", "disability_status",
            "previous_scholarship", "preferred_funding"
        ]

        values = [request.form.get(field, "").strip() for field in fields]

        if not name or not email or not values[0] or not values[1]:
            flash("Name, email, course and study year are required.", "error")
            return redirect(url_for("matched_scholarships"))

        try:
            # Validate marks and annual income: must be numeric and non-negative
            for index in [2, 3]:
                if values[index]:
                    number = float(values[index])
                    if number < 0:
                        raise ValueError(
                            "Marks and annual income cannot be negative."
                        )

            # Validate only actual percentage fields
            for index in [16, 17, 18]:
                if values[index]:
                    number = float(values[index])
                    if not 0 <= number <= 100:
                        raise ValueError(
                            "Percentages must be between 0 and 100."
                        )


            with get_db() as db:
                # Update the account's name and email.
                # Email must remain unique.
                db.execute(
                    "UPDATE users SET name=%s, email=%s WHERE id=%s",
                    (name, email, user_id)
                )

                db.execute("""
                    INSERT INTO student_profiles (
                        user_id, course, study_year, marks, annual_income,
                        state, category, date_of_birth, gender, phone, address,
                        city, district, pincode, domicile_state, college,
                        admission_year, tenth_percentage, twelfth_percentage,
                        previous_percentage, parent_guardian_name,
                        parent_occupation, minority_status, disability_status,
                        previous_scholarship, preferred_funding
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''),
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''),
                        %s, %s, %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        course=VALUES(course),
                        study_year=VALUES(study_year),
                        marks=VALUES(marks),
                        annual_income=VALUES(annual_income),
                        state=VALUES(state),
                        category=VALUES(category),
                        date_of_birth=VALUES(date_of_birth),
                        gender=VALUES(gender),
                        phone=VALUES(phone),
                        address=VALUES(address),
                        city=VALUES(city),
                        district=VALUES(district),
                        pincode=VALUES(pincode),
                        domicile_state=VALUES(domicile_state),
                        college=VALUES(college),
                        admission_year=VALUES(admission_year),
                        tenth_percentage=VALUES(tenth_percentage),
                        twelfth_percentage=VALUES(twelfth_percentage),
                        previous_percentage=VALUES(previous_percentage),
                        parent_guardian_name=VALUES(parent_guardian_name),
                        parent_occupation=VALUES(parent_occupation),
                        minority_status=VALUES(minority_status),
                        disability_status=VALUES(disability_status),
                        previous_scholarship=VALUES(previous_scholarship),
                        preferred_funding=VALUES(preferred_funding),
                        updated_at=CURRENT_TIMESTAMP
                """, [user_id] + values)

            session["user_name"] = name
            flash("Your complete student profile has been saved!", "success")
            return redirect(url_for("matched_scholarships"))
            

        except ValueError as error:
            flash(f"Please check the marks and income fields: {error}", "error")
        except IntegrityError:
            flash("This email address is already registered to another account.", "error")

    with get_db() as db:
        user = db.execute(
            "SELECT id, name, email FROM users WHERE id=%s",
            (user_id,)
        ).fetchone()

        profile_data = db.execute(
            "SELECT * FROM student_profiles WHERE user_id=%s",
            (user_id,)
        ).fetchone()

    return render_template(
        "profile.html",
        user=user,
        profile_data=profile_data
    )







@app.route("/tracker", methods=["GET", "POST"])
@login_required
def tracker():
    user_id = session["user_id"]
    allowed = {"Interested", "Preparing documents", "Ready to apply", "Applied", "Awarded", "Not selected"}
    if request.method == "POST":
        scholarship_id = request.form.get("scholarship_id", type=int)
        status = request.form.get("status", "Interested")
        notes = request.form.get("notes", "").strip()[:1000]
        if status not in allowed:
            abort(400)
        with get_db() as db:
            exists = db.execute("SELECT id FROM scholarships WHERE id = %s", (scholarship_id,)).fetchone()
            if not exists:
                abort(404)
            db.execute("""INSERT INTO applications (user_id, scholarship_id, status, notes)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status=VALUES(status), notes=VALUES(notes), updated_at=CURRENT_TIMESTAMP""",
                (user_id, scholarship_id, status, notes))
        flash("Application tracker updated.", "success")
        return redirect(url_for("tracker"))
    with get_db() as db:
        items = db.execute("""SELECT a.*, s.name, s.provider, s.deadline, s.official_url
            FROM applications a JOIN scholarships s ON s.id=a.scholarship_id
            WHERE a.user_id=%s ORDER BY a.updated_at DESC""", (user_id,)).fetchall()
        all_scholarships = db.execute("SELECT id, name FROM scholarships ORDER BY name").fetchall()
    return render_template("tracker.html", items=items, all_scholarships=all_scholarships, statuses=sorted(allowed))


@app.route("/compare", methods=["GET", "POST"])
def compare():
    selected = session.get("compare_ids", [])
    if request.method == "POST":
        action = request.form.get("action", "add")
        sid = request.form.get("scholarship_id", type=int)
        if action == "clear":
            session["compare_ids"] = []
            flash("Comparison list cleared.", "info")
        elif sid:
            with get_db() as db:
                exists = db.execute("SELECT id FROM scholarships WHERE id=%s", (sid,)).fetchone()
            if exists:
                selected = session.get("compare_ids", [])
                if action == "remove":
                    selected = [x for x in selected if x != sid]
                elif sid not in selected and len(selected) < 3:
                    selected.append(sid)
                elif sid not in selected:
                    flash("You can compare up to 3 scholarships at a time.", "error")
                session["compare_ids"] = selected
        return redirect(request.form.get("next") or url_for("compare"))
    selected = session.get("compare_ids", [])
    rows = []
    if selected:
        placeholders = ",".join(["%s"] * len(selected))
        with get_db() as db:
            rows = db.execute(f"SELECT * FROM scholarships WHERE id IN ({placeholders})", selected).fetchall()
    return render_template("compare.html", scholarships=rows)


@app.route("/export/saved.csv")
@login_required
def export_saved():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Scholarship", "Provider", "Region", "Education", "Award", "Deadline", "Official URL"])
    with get_db() as db:
        rows = db.execute("""SELECT s.name, s.provider, s.region, s.education, s.award, s.deadline, s.official_url
            FROM scholarships s JOIN saved_scholarships ss ON ss.scholarship_id=s.id
            WHERE ss.user_id=%s ORDER BY s.name""", (session["user_id"],)).fetchall()
        for row in rows:
            writer.writerow(list(row.values()))
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=scholarspot_saved_scholarships.csv"})


@app.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    matches = []
    answers = {"education": "", "region": "", "community": ""}
    if request.method == "POST":
        answers = {k: request.form.get(k, "").strip() for k in answers}
        sql = "SELECT * FROM scholarships WHERE 1=1"
        params = []
        if answers["education"]:
            sql += " AND (education = %s OR education = 'All levels')"
            params.append(answers["education"])
        if answers["region"]:
            sql += " AND (region = %s OR region = 'All India')"
            params.append(answers["region"])
        if answers["community"] and answers["community"] != "All communities":
            sql += " AND (community = %s OR community = 'All communities')"
            params.append(answers["community"])
        with get_db() as db:
            matches = db.execute(sql + " ORDER BY amount DESC", params).fetchall()
    return render_template("eligibility.html", matches=matches, answers=answers)


@app.route("/about")
def about():
    return render_template("about.html")


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page or scholarship could not be found."), 404


# Tables and initial demo rows are created in MySQL when the app starts.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
