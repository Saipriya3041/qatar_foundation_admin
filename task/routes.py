from flask import request, jsonify, render_template, redirect, url_for
from models import db, Admin, Opportunity
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer


# -----------------------
# HOME
# -----------------------
@app.route('/')
def home():
    return render_template('login.html')
@app.route('/')
def admin():
    return render_template('admin.html')


# -----------------------
# SIGNUP
# -----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'GET':
        return render_template('signup.html')   # must exist in templates

    data = request.form

    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm = data.get('confirm_password')

    if not all([full_name, email, password, confirm]):
        return "All fields required"

    if password != confirm:
        return "Passwords do not match"

    if len(password) < 8:
        return "Password must be at least 8 characters"

    if Admin.query.filter_by(email=email).first():
        return "Account already exists"

    hashed_pw = generate_password_hash(password)

    user = Admin(full_name=full_name, email=email, password_hash=hashed_pw)

    db.session.add(user)
    db.session.commit()

    return redirect(url_for('login'))


# -----------------------
# LOGIN
# -----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html')

    data = request.form

    user = Admin.query.filter_by(email=data.get('email')).first()

    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return "Invalid email or password"

    login_user(user, remember=True)

    return redirect(url_for('dashboard'))


# -----------------------
# DASHBOARD
# -----------------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# -----------------------
# LOGOUT
# -----------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# -----------------------
# FORGOT PASSWORD
# -----------------------
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.form

    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    user = Admin.query.filter_by(email=data.get('email')).first()

    if user:
        token = serializer.dumps(user.email, salt='reset')
        print("Reset link:", f"http://127.0.0.1:5000/reset/{token}")

    return "If email exists, reset link sent"


# -----------------------
# RESET TOKEN
# -----------------------
@app.route('/reset/<token>')
def reset(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    try:
        email = serializer.loads(token, salt='reset', max_age=3600)
        return f"Valid token for {email}"
    except:
        return "Token expired"


# -----------------------
# GET OPPORTUNITIES
# -----------------------
@app.route('/opportunities')
@login_required
def get_all():
    ops = Opportunity.query.filter_by(admin_id=current_user.id).all()
    return jsonify([{
        "id": op.id,
        "title": op.title,
        "category": op.category,
        "duration": op.duration,
        "start_date": op.start_date,
        "description": op.description
    } for op in ops])


# -----------------------
# ADD OPPORTUNITY
# -----------------------
@app.route('/opportunities/add', methods=['POST'])
@login_required
def add():
    data = request.form

    op = Opportunity(
        title=data.get('title'),
        duration=data.get('duration'),
        start_date=data.get('start_date'),
        description=data.get('description'),
        skills=data.get('skills'),
        category=data.get('category'),
        future_opportunities=True if data.get('future_opportunities') else False,
        max_applicants=data.get('max_applicants'),
        admin_id=current_user.id
    )

    db.session.add(op)
    db.session.commit()

    return "Opportunity Added"


# -----------------------
# DELETE
# -----------------------
@app.route('/opportunities/delete/<int:id>')
@login_required
def delete(id):
    op = Opportunity.query.get_or_404(id)

    if op.admin_id != current_user.id:
        return "Unauthorized"

    db.session.delete(op)
    db.session.commit()

    return "Deleted"