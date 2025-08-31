from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import os

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

class UserForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.rank == 'Admin':
            return redirect(url_for('admin_portal'))
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
    if current_user.rank != 'Employee':
        return 'Access restricted', 403
    return f'Welcome to your portal, {current_user.name}!'

@app.route('/admin_dashboard')
@login_required
def admin_portal():
    if current_user.rank != 'Admin':
        return 'Access restricted', 403
    return f'Welcome, Administrator {current_user.name}!'

@app.route('/initialize_db')
def initialize_db():
    with app.app_context():
        db.create_all()
        if not Employee.query.filter_by(name='admin').first():
            hashed_pw = generate_password_hash('admin_password')
            new_admin = Employee(name='admin', password_hash=hashed_pw, rank='Admin')
            db.session.add(new_admin)
            db.session.commit()
            return 'Initial admin user created successfully.'
        return 'Database and admin user already exist.'

if __name__ == '__main__':
    app.run(debug=True, port=5001)
