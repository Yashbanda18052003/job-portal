from flask import Flask, render_template, redirect, request, url_for, session, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from functools import wraps
import os
import json
from werkzeug.utils import secure_filename
import interview_engine

# Initialize app
app = Flask(__name__)
app.config.from_object('config')
app.secret_key = "1d56fb58fbce866d1c07ff3a9a113adb"
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Upload resume config
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'resumes')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_user():
    return dict(user=current_user, now=datetime.utcnow())


# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================
# MODELS
# ==========================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_employer = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    company = db.Column(db.String(200))  # Company name for employers
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(100))
    location = db.Column(db.String(100))
    category = db.Column(db.String(100))
    company = db.Column(db.String(200))
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employer = db.relationship('User', backref='jobs_posted')


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    resume = db.Column(db.String(300))
    status = db.Column(db.String(50), default='Pending')
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='applications')
    job = db.relationship('Job', backref='applications')


class MockInterview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    role_title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), default="Tech Corp")
    score = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(10), default="B")
    communication_score = db.Column(db.Integer, default=0)
    technical_score = db.Column(db.Integer, default=0)
    problem_solving_score = db.Column(db.Integer, default=0)
    code_score = db.Column(db.Integer, default=0)
    feedback_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='interviews')
    job = db.relationship('Job', backref='interviews')


# ==========================================
# DECORATORS & SEEDING
# ==========================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Administrator access required for this section.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def check_db_schema():
    try:
        db.create_all()
        from sqlalchemy import text
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(job);")).fetchall()
            cols = [r[1] for r in result]
            if 'status' not in cols:
                conn.execute(text("ALTER TABLE job ADD COLUMN status VARCHAR(50) DEFAULT 'Open';"))
                conn.commit()
    except Exception as e:
        print("Schema verification note:", e)


def create_admin():
    admin_email = 'admin@jobportal.com'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='admin',
            email=admin_email,
            is_admin=True,
            is_approved=True,
            company='JobPortal Administration'
        )
        admin.password = generate_password_hash('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin account verified: admin@jobportal.com / admin123")


# ==========================================
# ROUTES
# ==========================================
@app.route('/')
def index():
    query = Job.query
    
    # Filter parameters
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    location = request.args.get('location', '').strip()
    company = request.args.get('company', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if search:
        query = query.filter(
            (Job.title.ilike(f'%{search}%')) | 
            (Job.description.ilike(f'%{search}%')) |
            (Job.company.ilike(f'%{search}%'))
        )
    if category:
        query = query.filter(Job.category == category)
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    if company:
        query = query.filter(Job.company.ilike(f'%{company}%'))
        
    # Pagination: 5 jobs per page
    pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=5, error_out=False)
    jobs = pagination.items
    
    # Extract distinct categories for filter buttons/dropdown
    all_jobs = Job.query.all()
    job_categories = [j.category for j in all_jobs if j.category and j.category.strip()]
    popular_categories = ['Backend Engineering', 'Frontend Development', 'Software Engineering', 'Data Science & AI', 'UI/UX Design', 'Product Management', 'DevOps & Cloud']
    categories = sorted(list(set(popular_categories + job_categories)))
    
    return render_template(
        'index.html', 
        user=current_user, 
        jobs=jobs,
        pagination=pagination,
        categories=categories,
        search=search,
        category=category,
        location=location,
        company=company
    )


@app.route('/uploads/<filename>')
@app.route('/resume/<path:filename>')
@app.route('/resumes/<path:filename>', endpoint='resume_file')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        is_employer = request.form.get('is_employer') == 'on'
        company = request.form.get('company', '').strip() if is_employer else None

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('register'))

        if is_employer and not company:
            flash("Company name is required for employer registration.", "warning")
            return redirect(url_for('register'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email is already registered. Please log in.", "warning")
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            is_employer=is_employer,
            company=company
        )
        user.password = generate_password_hash(password)

        if not is_employer:
            user.is_approved = True  # Candidates auto-approved
        else:
            user.is_approved = False  # Employers need admin verification

        db.session.add(user)
        db.session.commit()

        if is_employer:
            flash("Employer account created! It will become active once approved by the administrator.", "info")
        else:
            flash("Registration successful! You can now log in and apply for jobs.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password. Please verify your credentials.", "danger")
            return redirect(url_for('login'))

        login_user(user)

        if user.is_admin:
            flash("Welcome, Administrator!", "success")
            return redirect(url_for('admin_dashboard'))

        if user.is_employer:
            if user.is_approved:
                flash(f"Welcome back, {user.company or user.username}!", "success")
                return redirect(url_for('post_job'))
            flash("Your employer account is currently pending administrator verification.", "info")
            return redirect(url_for('index'))

        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('index'))


@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    user = current_user
    if not user.is_employer:
        flash("Only verified employers can post job openings.", "danger")
        return redirect(url_for('index'))
    if not user.is_approved:
        flash("Your employer account is pending administrator approval before you can post jobs.", "warning")
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        salary = request.form.get('salary', '').strip()
        location = request.form.get('location', '').strip()
        category = request.form.get('category', '').strip()
        company = user.company or user.username

        if not title or not description:
            flash("Job title and description are required.", "danger")
            return redirect(url_for('post_job'))

        job = Job(
            title=title,
            description=description,
            salary=salary or "Competitive / Negotiable",
            location=location or "Remote",
            category=category or "General",
            company=company,
            posted_by=user.id
        )
        db.session.add(job)
        db.session.commit()
        flash("Job vacancy posted successfully!", "success")
        return redirect(url_for('index'))

    return render_template('post_job.html', user=current_user)


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)

    if current_user.is_admin:
        flash("Administrators cannot submit job applications.", "warning")
        return redirect(url_for('index'))
        
    if current_user.is_employer:
        flash("Employer accounts cannot apply for jobs. Please log in as a job seeker.", "warning")
        return redirect(url_for('index'))

    # Check for duplicate applications
    existing_application = Application.query.filter_by(
        user_id=current_user.id, job_id=job.id
    ).first()

    if existing_application:
        flash("You have already applied for this position. View status below.", "info")
        return redirect(url_for('my_applications'))

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file part detected in request.", "danger")
            return redirect(request.url)

        file = request.files['resume']

        if file.filename == '':
            flash("Please choose a PDF resume file to upload.", "warning")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            timestamp = int(datetime.utcnow().timestamp())
            unique_filename = f"resume_u{current_user.id}_j{job.id}_{timestamp}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            new_application = Application(
                user_id=current_user.id,
                job_id=job.id,
                resume=unique_filename
            )
            db.session.add(new_application)
            db.session.commit()

            flash("Application submitted successfully! Track your application below.", "success")
            return redirect(url_for('my_applications'))
        else:
            flash("Invalid file type. Please upload a PDF resume (.pdf only).", "danger")
            return redirect(request.url)

    # Clean GET request - NO FLASH MESSAGE ON LOAD
    return render_template('apply_job.html', job=job)


@app.route('/my-applications')
@login_required
def my_applications():
    user = current_user
    applications = Application.query.filter_by(user_id=user.id).order_by(Application.applied_on.desc()).all()
    return render_template('my_applications.html', applications=applications, user=user)


@app.route('/applications')
@login_required
def view_applications():
    user = current_user
    if not user.is_employer or not user.is_approved:
        flash("Only approved employers have access to candidate applications.", "danger")
        return redirect(url_for('index'))

    jobs = Job.query.filter_by(posted_by=user.id).all()
    job_ids = [job.id for job in jobs]
    applications = Application.query.filter(Application.job_id.in_(job_ids)).order_by(Application.applied_on.desc()).all() if job_ids else []

    return render_template('applications.html', user=user, applications=applications, jobs=jobs)


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    from collections import Counter
    
    # Global KPI totals
    total_candidates_count = User.query.filter_by(is_employer=False, is_admin=False).count()
    total_employers_count = User.query.filter_by(is_employer=True).count()
    pending_employers_count = User.query.filter_by(is_employer=True, is_approved=False).count()
    total_jobs_count = Job.query.count()
    total_applications_count = Application.query.count()

    # Pagination: 5 records per page for each table
    emp_page = request.args.get('emp_page', 1, type=int)
    app_page = request.args.get('app_page', 1, type=int)
    job_page = request.args.get('job_page', 1, type=int)

    employers_pag = User.query.filter_by(is_employer=True).order_by(User.date_created.desc()).paginate(page=emp_page, per_page=5, error_out=False)
    applications_pag = Application.query.order_by(Application.applied_on.desc()).paginate(page=app_page, per_page=5, error_out=False)
    jobs_pag = Job.query.order_by(Job.created_at.desc()).paginate(page=job_page, per_page=5, error_out=False)

    # Graphical Data aggregation
    all_applications = Application.query.all()
    status_distribution = {
        'Pending': sum(1 for a in all_applications if a.status == 'Pending'),
        'Under Review': sum(1 for a in all_applications if a.status == 'Under Review'),
        'Accepted': sum(1 for a in all_applications if a.status == 'Accepted'),
        'Rejected': sum(1 for a in all_applications if a.status == 'Rejected'),
    }

    all_jobs = Job.query.all()
    category_counts = dict(Counter(j.category or 'General' for j in all_jobs))

    users = {u.id: u for u in User.query.all()}

    return render_template(
        'admin.html',
        employers=employers_pag.items,
        employers_pag=employers_pag,
        jobs=jobs_pag.items,
        jobs_pag=jobs_pag,
        applications=applications_pag.items,
        applications_pag=applications_pag,
        users=users,
        total_candidates_count=total_candidates_count,
        total_employers_count=total_employers_count,
        pending_employers_count=pending_employers_count,
        total_jobs_count=total_jobs_count,
        total_applications_count=total_applications_count,
        status_distribution=status_distribution,
        category_distribution=category_counts
    )


@app.route('/approve/<int:user_id>')
@login_required
@admin_required
def approve_employer(user_id):
    employer = User.query.get_or_404(user_id)
    if employer.is_employer:
        employer.is_approved = True
        db.session.commit()
        flash(f"Employer '{employer.company or employer.username}' approved successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    flash("Action failed: user is not an employer.", "danger")
    return redirect(url_for('admin_dashboard'))


@app.route('/revoke/<int:user_id>')
@login_required
@admin_required
def revoke_employer(user_id):
    employer = User.query.get_or_404(user_id)
    if employer.is_employer:
        employer.is_approved = False
        db.session.commit()
        flash(f"Employer '{employer.company or employer.username}' permissions revoked.", "warning")
        return redirect(url_for('admin_dashboard'))
    flash("Action failed: user is not an employer.", "danger")
    return redirect(url_for('admin_dashboard'))


@app.route('/change_job_status/<int:job_id>/<new_status>')
@login_required
@admin_required
def change_job_status(job_id, new_status):
    job = Job.query.get_or_404(job_id)
    job.status = new_status
    db.session.commit()
    flash(f"Job status updated to '{new_status}'.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/change_application_status/<int:app_id>/<new_status>')
@login_required
def change_application_status(app_id, new_status):
    application = Application.query.get_or_404(app_id)
    is_job_owner = current_user.is_employer and (application.job and application.job.posted_by == current_user.id)
    
    if not (current_user.is_admin or is_job_owner):
        flash("Unauthorized action: You do not have permission to modify this application.", "danger")
        return redirect(url_for('index'))

    application.status = new_status
    db.session.commit()
    flash(f"Application #{app_id} status updated to '{new_status}'.", "success")
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('view_applications'))


# ==========================================
# AI MOCK INTERVIEW ROUTES
# ==========================================
@app.route('/interview-practice')
def interview_hub():
    """Hub for candidate interview practice: tracks, open jobs, and past records."""
    jobs = Job.query.filter_by(status='Open').order_by(Job.created_at.desc()).limit(12).all()
    user_interviews = []
    if current_user.is_authenticated:
        user_interviews = MockInterview.query.filter_by(user_id=current_user.id).order_by(MockInterview.created_at.desc()).limit(6).all()
    
    tracks = [
        {
            'key': 'backend',
            'title': 'Backend Engineering',
            'badge': '⚙️ Backend Systems',
            'desc': 'System design, database indexing, caching strategies, concurrency, and algorithmic problem-solving.',
            'role': 'Senior Backend Engineer (Python / Java / Go)'
        },
        {
            'key': 'frontend',
            'title': 'Frontend Engineering',
            'badge': '🎨 Frontend & UI',
            'desc': 'Core Web Vitals, state management, component lifecycles, DOM manipulation, and JavaScript logic.',
            'role': 'Senior Frontend Engineer (React / TypeScript)'
        },
        {
            'key': 'fullstack',
            'title': 'Full-Stack Development',
            'badge': '🌐 Full-Stack',
            'desc': 'End-to-end architecture, RESTful API design, authentication, CSRF/XSS, and database integration.',
            'role': 'Full-Stack Software Engineer'
        },
        {
            'key': 'data_ai',
            'title': 'Data Science & AI',
            'badge': '🤖 AI & Data',
            'desc': 'Machine learning pipelines, data drift, feature scaling, model metrics, and statistical coding challenges.',
            'role': 'Data Scientist & Machine Learning Engineer'
        },
        {
            'key': 'devops',
            'title': 'DevOps & Cloud',
            'badge': '☁️ DevOps & Cloud',
            'desc': 'Kubernetes orchestration, CI/CD pipelines, automated canary rollouts, and infrastructure reliability.',
            'role': 'Cloud Infrastructure & DevOps Engineer'
        },
        {
            'key': 'mobile',
            'title': 'Mobile Development',
            'badge': '📱 Mobile Engineering',
            'desc': 'Offline caching, mobile lifecycle management, memory leaks, and mobile algorithmic challenges.',
            'role': 'Mobile Application Engineer (iOS / Android / Flutter)'
        }
    ]
    return render_template('interview_hub.html', jobs=jobs, user_interviews=user_interviews, tracks=tracks)


@app.route('/interview/<int:job_id>')
def start_job_interview(job_id):
    """Launches the dual-round interview room tailored for a specific job."""
    job = Job.query.get_or_404(job_id)
    bundle = interview_engine.get_interview_bundle(job=job)
    return render_template(
        'interview_room.html',
        job=job,
        bundle=bundle,
        bundle_json=json.dumps(bundle)
    )


@app.route('/interview/custom')
def start_custom_interview():
    """Launches interview room for a selected domain track or custom role."""
    track = request.args.get('track', 'backend')
    role = request.args.get('role', '')
    
    default_roles = {
        'backend': 'Senior Backend Engineer (Python / Java / Go)',
        'frontend': 'Senior Frontend Engineer (React / TypeScript)',
        'fullstack': 'Full-Stack Web Developer',
        'data_ai': 'Data Scientist & AI Specialist',
        'devops': 'DevOps & Cloud Infrastructure Engineer',
        'mobile': 'Mobile Application Engineer'
    }
    
    chosen_role = role if role else default_roles.get(track, 'Software Engineer')
    bundle = interview_engine.get_interview_bundle(role_title=chosen_role, category=track.capitalize())
    return render_template(
        'interview_room.html',
        job=None,
        bundle=bundle,
        bundle_json=json.dumps(bundle)
    )


@app.route('/api/run-code', methods=['POST'])
def api_run_code():
    """Executes code via local or cloud compiler and returns output and diagnostics."""
    data = request.get_json() or {}
    language = data.get('language', 'python')
    code = data.get('code', '')
    custom_stdin = data.get('stdin', '')
    
    result = interview_engine.execute_code(language, code, custom_stdin)
    return jsonify(result)


@app.route('/api/submit-interview', methods=['POST'])
def api_submit_interview():
    """Evaluates candidate face-to-face and coding performance, generating detailed report."""
    data = request.get_json() or {}
    job_id = data.get('job_id')
    role_title = data.get('role_title', 'Software Engineer')
    company = data.get('company', 'Tech Innovations Inc.')
    answers = data.get('answers', [])
    code_submission = data.get('code_submission', {})
    
    job = db.session.get(Job, job_id) if job_id else None
    bundle = interview_engine.get_interview_bundle(job=job, role_title=role_title, company=company)
    
    evaluation = interview_engine.evaluate_candidate_session(bundle, answers, code_submission)
    
    if current_user.is_authenticated:
        try:
            mock = MockInterview(
                user_id=current_user.id,
                job_id=job.id if job else None,
                role_title=bundle.get('role_title', role_title),
                company=bundle.get('company', company),
                score=evaluation['overall_score'],
                grade=evaluation.get('grade', 'B'),
                communication_score=evaluation['dimension_scores']['communication'],
                technical_score=evaluation['dimension_scores']['technical_depth'],
                problem_solving_score=evaluation['dimension_scores']['problem_solving'],
                code_score=evaluation['dimension_scores']['code_correctness'],
                feedback_summary=json.dumps(evaluation)
            )
            db.session.add(mock)
            db.session.commit()
            evaluation['saved'] = True
            evaluation['interview_id'] = mock.id
        except Exception as e:
            db.session.rollback()
            evaluation['saved'] = False
            evaluation['save_error'] = str(e)
    else:
        evaluation['saved'] = False
        
    return jsonify({'success': True, 'evaluation': evaluation})


@app.route('/my-interviews')
@login_required
def my_interviews():
    """Displays candidate's historical interview scores, ratings, and AI feedback reports."""
    interviews = MockInterview.query.filter_by(user_id=current_user.id).order_by(MockInterview.created_at.desc()).all()
    
    # Parse feedback JSON summaries for display
    parsed_interviews = []
    for item in interviews:
        feedback = {}
        try:
            if item.feedback_summary:
                feedback = json.loads(item.feedback_summary)
        except Exception:
            feedback = {}
        parsed_interviews.append({
            'item': item,
            'feedback': feedback
        })
        
    return render_template('my_interviews.html', interviews=parsed_interviews)


# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        check_db_schema()
        create_admin()
        print("Database checked and admin account verified.")
    print("Starting Job Portal on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
