from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory




# Initialize app
app = Flask(__name__)
app.config.from_object('config')
app.secret_key = "1d56fb58fbce866d1c07ff3a9a113adb"

# Initialize extensions
db = SQLAlchemy(app)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#Upload resume
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'resumes')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.context_processor
def inject_user():
    return dict(user=current_user)


# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# MODELS
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_employer = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    company = db.Column(db.String(200))  # Added for employers
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(100))
    location = db.Column(db.String(200))
    category = db.Column(db.String(100))
    company = db.Column(db.String(200))
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', back_populates='job', lazy=True)
    employer = db.relationship('User', backref='jobs', lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    resume = db.Column(db.String(200), nullable=False)  # stores file path
    status = db.Column(db.String(20), default='Under Review')
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)  # ← Add this line


    # user = db.relationship('User', backref='applications', lazy=True)
    job = db.relationship('Job', back_populates='applications')
    job_seeker = db.relationship('User', backref='applications', lazy=True)
    


# ADMIN REQUIRED DECORATOR
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# CREATE DEFAULT ADMIN (runs once)
def create_admin():
    admin_email = 'admin@jobportal.com'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='admin',
            email=admin_email,
            is_admin=True,
            is_approved=True
        )
        admin.password = generate_password_hash('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin account created.")


# ROUTES
@app.route('/')
def index():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('index.html', user=current_user, jobs=jobs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        is_employer = request.form.get('is_employer') == 'on'
        company = request.form.get('company', '').strip() if is_employer else None

        if not username or not email or not password:
            return redirect(url_for('register', msg="Fill all required fields", type='error'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return redirect(url_for('register', msg="Username or email already exists", type='error'))

        user = User(
            username=username,
            email=email,
            is_employer=is_employer,
            company=company
        )
        user.password = generate_password_hash(password)

        if not is_employer:
            user.is_approved = True  # Job seekers auto-approved

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login', msg="Registered successfully", type='success'))

    return render_template('register.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return redirect(url_for('login', msg="Invalid credentials", type='error'))

        login_user(user)

        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        elif user.is_employer:
            if user.is_approved:
                return redirect(url_for('post_job'))
            else:
                return redirect(url_for('index', msg="Your employer account is not approved yet", type='info'))
        else:
            return redirect(url_for('index', msg="Logged in successfully", type='success'))

    return render_template('login.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index', msg="Logged out successfully", type='info'))


@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    user = current_user
    if not user.is_employer:
        return redirect(url_for('index', msg="Only employers can post jobs", type='error'))
    if not user.is_approved:
        return redirect(url_for('index', msg="Your employer account is not approved yet", type='error'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        salary = request.form.get('salary', '').strip()
        location = request.form.get('location', '').strip()
        category = request.form.get('category', '').strip()
        company = user.company or user.username

        if not title or not description:
            return redirect(url_for('post_job', msg="Title and description required", type='error'))

        job = Job(
            title=title,
            description=description,
            salary=salary,
            location=location,
            category=category,
            company=company,
            posted_by=user.id
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('index', msg="Job posted successfully", type='success'))

    return render_template('post_job.html', user=current_user)


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Check if the current user has already applied for this job
    existing_application = Application.query.filter_by(
        user_id=current_user.id, job_id=job.id
    ).first()

    if existing_application:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('my_applications'))

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)

        file = request.files['resume']

        if file.filename == '':
            flash('Please upload your resume before submitting.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_application = Application(
                user_id=current_user.id,
                job_id=job.id,
                resume=filename  # save only filename, not full path
            )
            db.session.add(new_application)
            db.session.commit()

            flash('Application submitted successfully!', 'success')
            return redirect(url_for('my_applications'))
        else:
            flash('Invalid file type. Please upload a PDF.', 'danger')

    return render_template('apply_job.html', job=job)



@app.route('/my-applications')
@login_required
def my_applications():
    user = current_user
    applications = Application.query.filter_by(user_id=user.id).all()
    return render_template('my_applications.html', applications=applications, user=user)


@app.route('/applications')
@login_required
def view_applications():
    user = current_user
    if not user.is_employer or not user.is_approved:
        return redirect(url_for('index', msg="Only approved employers can view applications", type='error'))

    jobs = Job.query.filter_by(posted_by=user.id).all()
    job_ids = [job.id for job in jobs]
    applications = Application.query.filter(Application.job_id.in_(job_ids)).all()

    return render_template('applications.html', user=user, applications=applications, jobs=jobs)


@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    employers = User.query.filter_by(is_employer=True).all()
    jobs = Job.query.all()
    applications = Application.query.all()
    return render_template('admin.html', employers=employers, jobs=jobs, applications=applications)

@app.route('/change_job_status/<int:job_id>/<string:new_status>')
@admin_required
def change_job_status(job_id, new_status):
    job = Job.query.get(job_id)
    if job:
        job.status = new_status
        db.session.commit()
        flash(f'Job status changed to {new_status}.', 'success')
    else:
        flash('Job not found.', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/change_application_status/<int:app_id>/<string:new_status>')
@admin_required
def change_application_status(app_id, new_status):
    app_record = Application.query.get_or_404(app_id)
    app_record.status = new_status
    db.session.commit()
    flash(f'Application status changed to {new_status}.', 'success')
    return redirect(url_for('admin_dashboard'))



@app.route('/approve/<int:user_id>')
@login_required
@admin_required
def approve_employer(user_id):
    employer = User.query.get_or_404(user_id)
    if employer.is_employer:
        employer.is_approved = True
        db.session.commit()
        return redirect(url_for('admin_dashboard', msg="Employer approved", type='success'))
    return redirect(url_for('admin_dashboard', msg="Invalid action", type='error'))


@app.route('/revoke/<int:user_id>')
@admin_required
def revoke_employer(user_id):
    employer = User.query.get_or_404(user_id)
    if employer.is_employer:
        employer.is_approved = False
        db.session.commit()
        return redirect(url_for('admin_dashboard', msg="Employer revoked", type='info'))
    return redirect(url_for('admin_dashboard', msg="Invalid action", type='error'))



# MAIN
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
        print("Database created successfully")
    app.run(debug=True)
