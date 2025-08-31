# Author:Rohith
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash

class AppConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_secret_key_that_you_should_change')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///leave_data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config.from_object(AppConfig)
db = SQLAlchemy(app)
auth_manager = LoginManager(app)
auth_manager.login_view = 'login_page'

@auth_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))

class Employee(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rank = db.Column(db.String(20), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True)
    managed_employees = db.relationship('Employee', backref=db.backref('manager', remote_side=[id]), lazy='dynamic')

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')

class UserForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class LeaveForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('End Date', validators=[DataRequired()], format='%Y-%m-%d')
    reason = TextAreaField('Reason for Leave', validators=[DataRequired()])
    submit = SubmitField('Submit Request')

@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.rank == 'Admin':
            return redirect(url_for('admin_portal'))
        elif current_user.rank == 'Manager':
            return redirect(url_for('manager_portal'))
        else:
            return redirect(url_for('employee_portal'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    user_form = UserForm()
    if user_form.validate_on_submit():
        person = Employee.query.filter_by(name=user_form.name.data).first()
        if person and check_password_hash(person.password_hash, user_form.password.data):
            login_user(person)
            if person.rank == 'Admin':
                return redirect(url_for('admin_portal'))
            elif person.rank == 'Manager':
                return redirect(url_for('manager_portal'))
            else:
                return redirect(url_for('employee_portal'))
        flash('Incorrect username or password')
    return render_template('login.html', user_form=user_form)

@app.route('/logout')
@login_required
def sign_out():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/employee_dashboard')
@login_required
def employee_portal():
    if current_user.rank not in ['Employee', 'Manager', 'Admin']:
        return 'Access restricted', 403
    return render_template('employee_dashboard.html')

@app.route('/apply_leave', methods=['GET', 'POST'])
@login_required
def apply_leave():
    if current_user.rank not in ['Employee', 'Manager', 'Admin']:
        return 'Access restricted', 403
    
    form = LeaveForm()
    if form.validate_on_submit():
        if form.start_date.data > form.end_date.data:
            flash('End date must be after start date.')
            return render_template('apply_leave.html', form=form)
        
        leave_request = LeaveRequest(
            employee_id=current_user.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
            status='Pending'
        )
        db.session.add(leave_request)
        db.session.commit()
        flash('Your leave request has been submitted!')
        return redirect(url_for('my_requests'))

    return render_template('apply_leave.html', form=form)

@app.route('/my_requests')
@login_required
def my_requests():
    if current_user.rank not in ['Employee', 'Manager', 'Admin']:
        return 'Access restricted', 403
    
    requests = LeaveRequest.query.filter_by(employee_id=current_user.id).order_by(LeaveRequest.start_date.desc()).all()
    return render_template('my_requests.html', requests=requests)

@app.route('/manager_dashboard')
@login_required
def manager_portal():
    if current_user.rank != 'Manager':
        return 'Access restricted', 403
    
    managed_employees = current_user.managed_employees.all()
    managed_employee_ids = [emp.id for emp in managed_employees]
    
    pending_requests = LeaveRequest.query.filter(
        LeaveRequest.employee_id.in_(managed_employee_ids),
        LeaveRequest.status == 'Pending'
    ).order_by(LeaveRequest.start_date.asc()).all()
    
    return render_template('manager_dashboard.html', pending_requests=pending_requests)

@app.route('/approve/<int:request_id>')
@login_required
def approve_request(request_id):
    if current_user.rank != 'Manager':
        return 'Access restricted', 403
    
    req = LeaveRequest.query.get_or_404(request_id)
    if req.employee.manager_id != current_user.id:
        return 'Access restricted', 403
    
    req.status = 'Approved'
    db.session.commit()
    flash(f"Leave request for {req.employee.name} has been approved.")
    return redirect(url_for('manager_portal'))

@app.route('/reject/<int:request_id>')
@login_required
def reject_request(request_id):
    if current_user.rank != 'Manager':
        return 'Access restricted', 403
    
    req = LeaveRequest.query.get_or_404(request_id)
    if req.employee.manager_id != current_user.id:
        return 'Access restricted', 403
    
    req.status = 'Rejected'
    db.session.commit()
    flash(f"Leave request for {req.employee.name} has been rejected.")
    return redirect(url_for('manager_portal'))

@app.route('/admin_dashboard')
@login_required
def admin_portal():
    if current_user.rank != 'Admin':
        return 'Access restricted', 403
    
    all_users = Employee.query.all()
    all_requests = LeaveRequest.query.order_by(LeaveRequest.start_date.desc()).all()
    
    return render_template('admin_dashboard.html', all_users=all_users, all_requests=all_requests)

@app.route('/initialize_db')
def initialize_db():
    db.drop_all()
    db.create_all()

    admin_pass = generate_password_hash('admin_password')
    admin = Employee(name='admin', password_hash=admin_pass, rank='Admin')
    db.session.add(admin)
    db.session.commit()
    
    manager_pass = generate_password_hash('manager_password')
    manager = Employee(name='manager', password_hash=manager_pass, rank='Manager')
    db.session.add(manager)
    db.session.commit()
    
    emp1_pass = generate_password_hash('employee1_password')
    employee1 = Employee(name='john_doe', password_hash=emp1_pass, rank='Employee', manager_id=manager.id)
    
    emp2_pass = generate_password_hash('employee2_password')
    employee2 = Employee(name='jane_smith', password_hash=emp2_pass, rank='Employee', manager_id=manager.id)
    
    db.session.add_all([employee1, employee2])
    db.session.commit()

    leave1 = LeaveRequest(employee_id=employee1.id, start_date=datetime(2025, 10, 20), end_date=datetime(2025, 10, 25), reason='Family vacation', status='Pending')
    leave2 = LeaveRequest(employee_id=employee2.id, start_date=datetime(2025, 9, 5), end_date=datetime(2025, 9, 7), reason='Medical appointment', status='Approved')
    db.session.add_all([leave1, leave2])
    db.session.commit()
    
    return 'Database initialized successfully with sample users and data.'

if __name__ == '__main__':
    app.run(debug=True, port=5001)
