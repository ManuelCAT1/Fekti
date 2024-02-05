from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from .models import User, School
from . import db, Mail  # Import mail
from flask_login  import login_user, login_required, logout_user, current_user, UserMixin
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from . import URLSafeTimedSerializer

from flask import current_app as app




auth = Blueprint('auth', __name__)






@auth.route('/login', methods=['GET', 'POST'])
def loginPage():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if password == user.password:
                if user.confirmed:
                    flash('Zalogowano się!', category='success')
                    login_user(user, remember=True)
                    session['school_id'] = user.school_id
                    session['username'] = user.username  # Set username in session
                    return redirect(url_for('views.homePage'))
                else:
                    flash('Potwierdź swój email przed zalogowaniem', category='error')
            else:
                flash('Zła nazwa użytkownika lub hasło', category='error')
        else:
            flash('Zła nazwa użytkownika lub hasło', category='error')

        return redirect(url_for('auth.loginPage'))

    else:
        return render_template("index.html")

        





@auth.route('/register', methods=['GET', 'POST'])
def registerPage():
    if current_user.is_authenticated:
        return redirect(url_for('views.homePage'))
    schools = School.query.all()
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        school_id = request.form.get('school')
        school = School.query.get(school_id)
        if not school:
            flash('Zła szkoła', category='error')
            return render_template("register.html", schools=schools)

        user_email = User.query.filter_by(email=email).first()
        user_username = User.query.filter_by(username=username).first()

        if user_email:
            flash('Email już istnieje w bazie danych.', category='error')
        elif user_username:
            flash('Nazwa użytkownika już istnieje.', category='error')
        elif len(email) < 4:
            flash('Email musi być dluższy niż 3 znaki.', category='error')
        elif len(username) < 3:
            flash('Nazwa użytkownika musi być dluższa niż 2 znaki.', category='error')
        elif password != password2:
            flash('Hasła nie są takie same.', category='error')
        elif len(password) < 7:
            flash('Hasło musii być dłuższe niż 6 znaków.', category='error')
        else:
            new_user = User(email=email, username=username, password=password, school=school)
            db.session.add(new_user)
            db.session.commit()

            from . import s, mail

            token = s.dumps(email, salt='FektySaltSPXD')
            msg = Message('Potwierdź konto Fekti', sender='weryfikacja@fekti.com', recipients=[email])

            link = url_for('auth.confirm_email', token=token, _external=True)   

            msg.body= 'Twój link weryfikacyjny to {}'.format(link)


            mail.send(msg)
    
            
            logout_user()
            flash('Stworzono konto! Sprawdź maila, by je potwierdzić.', category='success')
            return redirect(url_for('auth.loginPage'))

    return render_template("register.html", schools=schools)


@auth.route('/weryfikacja/<token>')
def confirm_email(token):
    from . import s
    try:
        # Notice the omission of the max_age parameter
        email = s.loads(token, salt='FektySaltSPXD')
        user = User.query.filter_by(email=email).first()
        if user:
            user.confirmed = True  # Set the 'confirmed' attribute to True
            db.session.commit()  # Commit the change to the database
        else:
            return 'Invalid or expired token.', 400  # Handle non-existing user
    except SignatureExpired:
        # This block will no longer be necessary if max_age is omitted
        return render_template('expired.html')
    except:  # Catch other exceptions, such as BadSignature
        return 'Invalid or expired token.', 400
    return render_template('verification.html')


@auth.route('/logout')
@login_required
def logoutPage():
    if current_user.banned:
        return render_template('banned.html')
    logout_user()
    return redirect(url_for('auth.loginPage'))

