# Scholar Spot — Flask Scholarship Finder

A beginner-friendly multi-page scholarship discovery project built with Python Flask, HTML, CSS, JavaScript, and SQLite.

## Pages and features
- Home page
- Scholarship directory with keyword search and filters
- Scholarship detail pages
- Student registration and login
- Student dashboard with saved scholarships
- Admin dashboard to add, edit and delete scholarship records
- SQLite database automatically created on first run
- Passwords stored as secure hashes

## Run on Windows / VS Code

1. Install Python 3.10+ from https://www.python.org/downloads/ and enable "Add Python to PATH".
2. Extract this ZIP.
3. Open the `ScholarSpot_Flask_Project` folder in VS Code.
4. Open Terminal → New Terminal.
5. Run:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.
7. Stop the server with Ctrl+C in the terminal.

If PowerShell blocks virtual environment activation, run this in that terminal:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
Then activate again.

## Demo admin login
- Email: `admin@scholarspot.in`
- Password: `Admin@123`

Change the demo admin password and Flask SECRET_KEY before using this outside a local classroom demo. This starter does not include email verification, password reset, CSRF protection, or production deployment configuration.

## Important scholarship-data note
Several entries are explicitly demo records. Verify every real scholarship's eligibility, status, award, deadline and application URL with the official provider. The site does not automatically scrape Scholarship For Me or any other website.

## Database
SQLite file `scholarspot.db` is created automatically next to `app.py`. To reset the sample database, stop Flask and delete that file; it will be recreated next time you run `python app.py`. This deletes local accounts and saved scholarships too.


## Additional features in this version
- Student profile page to save education level, study year, marks/CGPA, annual family income, state and optional category.
- Scholarship matcher that filters records by education, region and community. It is a discovery aid, not an official eligibility decision.
- Compare up to three scholarships side by side.
- Application tracker with statuses and personal notes.
- Export saved scholarships to a CSV file for Excel.
- Responsive layouts for new pages.

## New routes
- `/profile` — edit your student profile (login required)
- `/eligibility` — filter potential scholarship matches
- `/compare` — compare selected scholarships
- `/tracker` — track application progress (login required)
- `/export/saved.csv` — download saved scholarships (login required)

The seeded demo entries are examples only. Verify deadlines, eligibility and awards on official provider websites. The demo admin credentials are for local development only; change them before deployment.
