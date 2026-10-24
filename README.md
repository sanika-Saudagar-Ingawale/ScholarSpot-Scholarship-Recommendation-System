# ScholarSpot – Student Scholarship Recommendation System

## 📌 Project Overview

ScholarSpot is a web-based Student Scholarship Recommendation System developed using Python, Flask, MySQL, HTML, CSS, and Bootstrap.

The system helps students find relevant scholarship opportunities based on their educational and personal profile. It compares student information with scholarship criteria and ranks matching scholarships using a rule-based recommendation algorithm with weighted scoring.

The main goal of the project is to make scholarship discovery easier, more organized, and more accessible for students.

## 🎯 Objectives

- Simplify the scholarship search process.
- Recommend scholarships based on student profile information.
- Match educational level, location, and category with scholarship criteria.
- Rank scholarships according to their match scores.
- Store student profiles and scholarship information in a database.
- Provide a user-friendly interface for exploring scholarship opportunities.

## ✨ Features

- Student registration and login.
- Student profile management.
- Scholarship listing and search.
- Profile-based scholarship recommendations.
- Rule-based matching and weighted scoring.
- Filtering and ranking of matching scholarships.
- Scholarship details and eligibility information.
- Save scholarships for later reference.
- Admin functionality for managing scholarship records.
- MySQL database integration.

Note: Include only the features implemented in your current version.

## 🧠 Recommendation Algorithm

The system uses a Rule-Based Scholarship Recommendation Algorithm with Weighted Scoring, Filtering, and Ranking.

### 1. Rule-Based Matching
The system checks whether student profile information matches scholarship criteria.

### 2. Weighted Scoring
The current matching logic assigns weights to selected criteria:

- Education match: 40 points
- Location match: 30 points
- Category match: 30 points

### 3. Match Score Formula

Match Score = (40 × E) + (30 × L) + (30 × C)

Where:
- E = 1 if education matches; otherwise 0.
- L = 1 if location matches; otherwise 0.
- C = 1 if category matches; otherwise 0.

### 4. Filtering
Scholarships with a match score greater than zero are selected by the current recommendation logic.

### 5. Ranking
The selected scholarships are sorted in descending order of their match scores.

Important: The match score indicates how closely selected profile fields match the scholarship record. It is not a probability of receiving the scholarship or confirmation of official eligibility. All applicable official eligibility conditions must be verified separately.

## 🛠️ Technologies Used

- **Programming Language:** Python
- **Web Framework:** Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, Bootstrap
- **Template Engine:** Jinja2
- **Database Connectivity:** MySQL Connector/Python
- **Development Tools:** Visual Studio Code and MySQL Workbench

## 🗄️ Database

The application uses MySQL to store and manage application data.

Depending on the current implementation, tables may include:

- `users` – user account information
- `student_profiles` – student profile details
- `scholarships` – scholarship records
- `saved_scholarships` – saved scholarship records
- `applications` – application tracking information, if implemented

Create the database and tables using your project's actual SQL schema before running the application.

## ⚙️ Installation and Setup

### Prerequisites

Install the following software:

- Python 3
- MySQL Server
- MySQL Workbench
- Git
- Visual Studio Code (recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/ScholarSpot-Scholarship-Recommendation-System.git
cd ScholarSpot-Scholarship-Recommendation-System
```

Replace `YOUR-USERNAME` with your GitHub username.

### Step 2: Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure MySQL

1. Open MySQL Workbench.
2. Connect to your local MySQL server.
3. Create the database configured in your application, such as `scholarship_db`.
4. Create the required tables using your project's SQL schema.
5. Configure database credentials through environment variables.

Example `.env` settings:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=scholarship_db
SECRET_KEY=replace_with_a_secure_random_value
```

Use the variable names expected by your application. Never upload your real `.env` file or database password to GitHub.

### Step 5: Run the Application

```bash
python app.py
```

Open the local address displayed in the terminal, commonly:

```text
http://127.0.0.1:5000
```

## 📂 Project Structure

The structure depends on the actual files in your repository. A typical layout is:

```text
ScholarSpot-Scholarship-Recommendation-System/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   └── matched_scholarships.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── database/
    └── schema.sql
```

Keep only the folders and filenames that actually exist in your project. Add `database/schema.sql` only if you have prepared the SQL schema file.

## 🔒 Security Considerations

- Never publish database passwords, API keys, or secret keys.
- Store sensitive configuration in environment variables.
- Use password hashing for user passwords.
- Validate user inputs.
- Use parameterized SQL queries.
- Do not upload private student data or production database backups.

## 🚀 Future Enhancements

- Add more verified scholarship opportunities with official source links.
- Improve eligibility checking for marks, family income, domicile, and other applicable criteria.
- Add scholarship deadline notifications.
- Support multiple languages.
- Improve recommendation explanations.
- Explore content-based filtering or machine learning after collecting suitable, reliable data.

## ⚠️ Disclaimer

This project is intended to help students discover potentially relevant scholarships. Recommendations are based on the information available in the database and the implemented matching rules. Students should verify current eligibility, deadlines, required documents, and application procedures on the official scholarship portal before applying.

## 👩‍💻 Author

**Your Name:** Replace with your name  
**GitHub:** Add your GitHub profile URL

## 📄 License

Choose a license before distributing or reusing this project. For example, you may use the MIT License by adding a `LICENSE` file with its complete text.

