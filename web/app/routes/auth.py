from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from app.extensions import db
from app.models import User, Student, Teacher
from app.utils.helpers import hash_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = hash_password(password)
        
        user = User.query.filter_by(username=username, password=hashed).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            
            if user.role == 'student':
                student = user.student
                if student:
                    session['name'] = student.name
                    session['class_id'] = student.class_id
                    session['gender'] = student.gender
                    session['class_name'] = student.class_.name if student.class_ else ""
                    session['roll_no'] = student.roll_no
                    return redirect(url_for('student.dashboard'))
            
            elif user.role == 'teacher':
                teacher = user.teacher
                if teacher:
                    session['name'] = teacher.name
                    session['gender'] = teacher.gender
                    return redirect(url_for('teacher.dashboard'))
            
            elif user.role == 'admin':
                session['name'] = "Admin"
                return redirect(url_for('admin.dashboard'))
                
        flash("Invalid credentials", "error")
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return redirect(url_for('auth.signup'))

        try:
            new_user = User(username=username, password=hash_password(password), role=role)
            db.session.add(new_user)
            db.session.flush() # Flush to get the new_user.id
            
            if role == 'student':
                new_student = Student(
                    name=request.form.get('name'),
                    roll_no=request.form.get('roll_no'),
                    gender=request.form.get('gender'),
                    user_id=new_user.id
                )
                db.session.add(new_student)
                
            elif role == 'teacher':
                new_teacher = Teacher(
                    name=request.form.get('name'),
                    gender=request.form.get('gender'),
                    user_id=new_user.id
                )
                db.session.add(new_teacher)
                
            db.session.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
            
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('auth.login'))