# Leavve Management System
### Python Flask - Role-Based Web Application 🚀

#### Project Description
This is a foundational web application built with Python 🐍 and the Flask framework. The project is designed as a secure, minimalist starter template for any application requiring user authentication with distinct roles. It provides a robust and clean architecture for managing user access, making it an ideal starting point for more complex systems like a leave management portal, an internal company dashboard, or a collaborative project tool.

---

#### Key Features
* **Role-Based Access Control** 🛡️: Differentiates between 'Admin' and 'Employee' users, directing them to separate, role-specific dashboards upon login.
* **Secure Authentication** 🔒: Users can log in with a unique username and password. Passwords are not stored in plain text but are hashed using `werkzeug.security` to ensure data integrity.
* **Database Management** 🗄️: Utilizes Flask-SQLAlchemy to manage a SQLite database, providing a lightweight, file-based storage solution that is easy to set up and manage.
* **Modular Code Structure** 🧩: The application's logic is contained within a single `app.py` file for simplicity and ease of use, with a clear separation between routes, models, and forms.
* **Session Management** 👤: Implements Flask-Login to handle user sessions, keeping users securely logged in across requests.
* **Temporary Database Setup** 🔧: Includes a one-time use route to initialize the database and create a default admin user, streamlining the initial setup process.

---

#### Technologies Used
* **Backend**: Python 🐍, Flask
* **Database**: SQLite
* **ORM**: Flask-SQLAlchemy
* **User Authentication**: Flask-Login, `werkzeug.security`
* **Forms**: Flask-WTF, WTForms

This project is a solid foundation that can be easily extended with more features, such as CRUD operations for data, user profiles, or custom functionalities tailored to your specific needs. ✨
