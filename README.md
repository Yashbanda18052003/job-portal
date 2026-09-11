# Job Portal Web Application

## Overview
A web-based recruitment job portal built with Python and Flask. The platform enables job seekers to explore open listings and submit applications with uploaded resumes, while allowing employers and admins to post job openings and review candidate submissions.

## Features
- **User Authentication:** Registration and authentication for Job Seekers and Employers/Admins using password hashing.
- **Job Postings Management:** Employers can create, update, and manage job listings with location, salary, and qualification requirements.
- **Application Workflow:** Applicants can apply to open positions and attach PDF resumes.
- **Applicant Management:** Employers can review candidate profiles, inspect submitted resumes, and track application records.
- **Admin Panel:** Administrative interface for overseeing job postings and portal users.

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Database:** SQLite (Development) / MySQL compatible
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap

## Project Structure
```
job-portal/
├── app.py              # Application entry point & route definitions
├── config.py           # Application configurations
├── requirements.txt    # Python dependencies list
├── static/             # CSS styling, JS scripts, and uploaded media
├── templates/          # HTML Jinja2 templates (Job views, Admin panel)
└── instance/           # Local SQLite instance (Development only)
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Yashbanda18052003/job-portal.git
   cd job-portal
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv env
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_random_secret_key
DATABASE_URL=sqlite:///instance/jobportal.db
```

## Database Setup

Initialize database tables automatically on first run via Flask-SQLAlchemy:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## How to Run

```bash
python app.py
```
Navigate to `http://127.0.0.1:5000` in your web browser.

## Screenshots
*(Add project screenshots here)*

## Future Improvements
- Migration of resume storage from local disk to AWS S3 or Cloudinary.
- Email notifications for applicants when job status changes.
- Keyword-based search and skill filtering for job listings.

## Author
**Yash Banda**  
LinkedIn: [linkedin.com/in/yash-banda-829633259](https://www.linkedin.com/in/yash-banda-829633259/)
