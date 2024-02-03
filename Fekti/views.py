from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import db, Photo, Like, School, User, Unlock, Report, PhotoFeedback, NeededFeedback
from Fekti.views import custom_b64encode

import os
from datetime import datetime, timedelta


import base64

def custom_b64encode(value):
    return base64.b64encode(value.encode('utf-8')).decode('utf-8')


from PIL import Image, ImageFilter
import io

import logging

logging.basicConfig(filename='routeLogs.log', level=logging.INFO)

def blur_image_blob(image_blob):
    # Convert the binary data to an image
    img = Image.open(io.BytesIO(image_blob))

    # Apply the blur filter
    blurred = img.filter(ImageFilter.GaussianBlur(35))

    # Save the blurred image to a BytesIO object
    byte_arr = io.BytesIO()
    blurred.save(byte_arr, format=img.format)  # Use the original image's format

    # Convert the BytesIO object to bytes
    blurred_blob = byte_arr.getvalue()

    return blurred_blob





ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

views = Blueprint('views', __name__)

@views.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@views.template_filter('custom_b64encode')
def custom_b64encode_filter(value):
    return custom_b64encode(value)


@views.route('/', defaults={'subject': None}, methods=['GET', 'POST'])
@views.route('/home', defaults={'subject': None})
@views.route('/home/<subject>')
@login_required
def homePage(subject):
    try:
        print("homePage 1")
        logging.info('Entered homePage() function')
        if current_user.banned:
            return render_template('banned.html')
        update_credits(current_user)
        school_id = session.get('school_id')
        photo = Photo(title="", fileName="", description="", school_id=None, user_id=None, image_data=None, school=None, credits=0, likes=[], selected_subject="")
        unlocked_photos_ids = [photo.id for photo in Photo.query.join(Unlock).filter(Unlock.user_id == current_user.id).all()]
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(school_id=current_user.school_id).order_by(Photo.likes_count.desc()).paginate(page=page, per_page=10)

        needed_feedback = NeededFeedback.query.filter_by(user_id=current_user.id, isRated=False).first()
        if needed_feedback:
            return flashFeedback(photo_id=needed_feedback.photo_id, user_id=current_user.id)

        # Apply the blur filter to each photo unless it's unlocked
        for photo in photos.items:
            if photo.id not in unlocked_photos_ids:
                photo.image_data = blur_image_blob(photo.image_data)

        if school_id is None or current_user.school_id != school_id:
            return redirect(url_for('auth.loginPage'))

        if subject is not None:
            photos = Photo.query.filter_by(school_id=current_user.school_id, selected_subject=subject).order_by(Photo.likes_count.desc()).paginate(page=page, per_page=10)
        else:
            photos = Photo.query.filter_by(school_id=current_user.school_id).order_by(Photo.likes_count.desc()).paginate(page=page, per_page=10)

        if current_user.school_id != session['school_id']:
            return redirect(url_for('views.homePage', school_id=session['school_id']))

        return render_template("home.html", photos=photos, photo=photo, user=current_user, unlocked_photos_ids=unlocked_photos_ids, credits=current_user.credits, selected_subject=subject, subjects=["Matematyka", "Fizyka", "Angielski", "Polski", "Hiszpański", "Niemiecki", "EDBiBHP", "Chemia", "Geografia", "Biologia", "Historia", "HITiWOS", "Informatyka", "Religia"])
    except Exception as e:
        with open('error.txt', 'w') as f:
            f.write(str(e))
        raise e  # Re-raise the exception after writing to the file

@views.route('/image/<int:photo_id>')
@login_required
def serve_image(photo_id):
    print("serve_image 2")
    logging.info('Entered image/() function')
    unlocked_photos_ids = [photo.id for photo in Photo.query.join(Unlock).filter(Unlock.user_id == current_user.id).all()]
    photo = Photo.query.get(photo_id)
    print(current_user.id)
    print(photo.image_id)

    

    if photo.id not in unlocked_photos_ids or photo.user_id != current_user.id:
        image_data = blur_image_blob(photo.image_data)
    elif photo.user_id == current_user.id:
        image_data = photo.image_data
        
    else:
        image_data = photo.image_data

    return send_file(io.BytesIO(image_data), mimetype='image/jpeg')

from datetime import datetime, timedelta

def update_credits(user):
    print("update_credits 3")
    logging.info('Entered update credits() function')
    if user.last_credit_update is not None and user.last_credit_update + timedelta(weeks=2) <= datetime.now():
        user.credits += 1
        user.last_credit_update = datetime.now()
        db.session.commit()

from flask import session
from datetime import datetime, timedelta



def flashFeedback(photo_id, user_id):
    print("flashFeedback 4")

    return redirect(url_for('views.feedback', photo_id=photo_id))

import schedule
import time


@views.route('/unlock_photo/<int:photo_id>', methods=['POST'])
@login_required
def unlock_photo(photo_id):
    print("unlock_photo 5")
    logging.info('Entered unlocktphoto() function')
    user = current_user
    photo = Photo.query.get(photo_id)
    
    
    if user.credits > 0:
        user.credits -= 1
        unlock = Unlock(user_id=user.id, photo_id=photo.id)
        db.session.add(unlock)
        db.session.commit()
        flash('Odblokowano zdjęcie', 'success')

        # Set the session variable
        session['unlocked_photo_id'] = photo_id


        schedule.every(1).day.do(add_photo_to_feedback, photo_id=photo_id, user_id=user.id)

 
        return redirect(url_for('views.Photos'))

    elif user.credits == 0:
        flash('Niewystarczające kredyty', 'error')
        return redirect(url_for('views.homePage'))

def add_photo_to_feedback(photo_id, user_id):
    print("add_photo_to_feedback 6")
    # Add the photo to the NeededFeedback table
    needed_feedback = NeededFeedback(photo_id=photo_id, user_id=user_id)
    db.session.add(needed_feedback)
    db.session.commit()


from datetime import datetime

@views.route('/feedback')
@login_required
def feedback():
    print("feedback 7")
    logging.info('Entered feedback() function')
    needed_feedback = NeededFeedback.query.filter_by(user_id=current_user.id).first()
    photo_id = needed_feedback.photo_id if needed_feedback else None

    if photo_id is None or (needed_feedback and needed_feedback.isRated):
        return redirect(url_for('views.homePage'))

    photo = Photo.query.get(photo_id)
    return render_template('feedback.html', photo=photo)

from flask import redirect, url_for

@views.route('/feedback_photo/<int:photo_id>')
@login_required
def feedback_photo(photo_id):
    print("feedback_photo 8")
    logging.info('Entered feedback pgohto() function')
    photo = Photo.query.get(photo_id)
    existing_feedback = PhotoFeedback.query.filter_by(photo_id=photo_id, user_id=current_user.id).first()
    if existing_feedback:
        flash('Już oceniłeś tego posta', 'error')
        return redirect(url_for('views.Photos'))
        

    if photo:
        return redirect(url_for('views.feedback', photo_id=photo_id))
    else:
        # Handle the case where the photo does not exist
        return "Photo not found"


@views.route('/submit_feedback/<int:photo_id>', methods=['POST'])
@login_required
def submit_feedback(photo_id):
    print("submit_feedback 9")
    logging.info('Entered submitfeedbacks() function')
    feedback = request.form.get('feedback')  # Get the feedback from the form
    feedback = True if feedback == 'like' else False


    photo = Photo.query.get(photo_id)

    if feedback == 'like':
        # Increment the like count
        photo.likes_count += 1
    elif feedback == 'dislike':
        photo.likes_count -= 1
    # Create a new PhotoFeedback record
    photo_feedback = PhotoFeedback(photo_id=photo_id, user_id=current_user.id, feedback=feedback)
    db.session.add(photo_feedback)
    db.session.commit()

    # Check if the photo has reached the threshold for likes or dislikes
    likes = PhotoFeedback.query.filter_by(photo_id=photo_id, feedback=True).count()
    dislikes = PhotoFeedback.query.filter_by(photo_id=photo_id, feedback=False).count()
    school_users = User.query.filter_by(school_id=photo.school_id).count()

    if likes >= 5 or (school_users >= 4 and likes / school_users >= 0.7):
        # Give 1 credit to the user who uploaded the photo
        user = User.query.get(photo.user_id)
        user.credits += 1
        db.session.commit()

    if dislikes >= 5:
        # Mark the photo as removed
        photo = Photo.query.get(photo_id)
        photo.removed = True
        db.session.commit()

        # Count the uploader's removed photos
        removed_photos = Photo.query.filter_by(user_id=photo.user_id, removed=True).count()

        if removed_photos >= 5:
            # Ban the uploader
            uploader = User.query.get(photo.usmainer_id)
            uploader.banned = True
            db.session.commit()

    NeededFeedback.query.filter_by(photo_id=photo_id, user_id=current_user.id).update({NeededFeedback.isRated: True})
    db.session.commit()
    session.pop('unlocked_photo_id', None)
    session.pop('unlock_time', None)


    return redirect(url_for('views.homePage'))

def mark_feedback_as_rated(photo_id, user_id):
    print("mark_feedback_as_rated 10")
    needed_feedback = NeededFeedback.query.filter_by(photo_id=photo_id, user_id=user_id).first()
    if needed_feedback:
        needed_feedback.isRated = True
        db.session.commit()


@views.route('/yourschool')

@views.route('/twojaszkola')

@views.route('/szkola')
@views.route('/school')
@login_required
def yourschool():
    print("yourschool 11")
    if current_user.banned:
        return redirect(url_for('views.banned'))  # Redirect to banned page

    school = current_user.school
    users = school.get_mainusers()
    return render_template('yourschool.html', users=users, credits=current_user.credits)

@views.route('/photos')
@views.route('/zdjecia')

@login_required
def photos():
    print("photos 12")
    if current_user.banned:
        return redirect(url_for('views.banned'))  # Redirect to banned page

    return render_template('photos.html', credits=current_user.credits)

# @views.route('/school')
# def school():
#     return render_template('schools/windows.html')
@views.route('/o-nas')
@views.route('/onas')
@views.route('/about')
def about():
    print("about 13")
    return render_template('about.html')

@views.route('/kontakt')
@views.route('/contact')
def contact():
    print("contact 14")
    return render_template('contact.html')

@views.route('/credits')
@views.route('/zetony')

@login_required
def credits():
    return render_template('credits.html')



@views.route('/like/<int:photo_id>', methods=['POST'])
@login_required
def like_photo(photo_id):
    like = Like.query.filter_by(user_id=current_user.id, photo_id=photo_id).first()
    if like:
        # If a Like record exists, delete it
        db.session.delete(like)
        
    else:
        # If no Like record exists, create one
        like = Like(user_id=current_user.id, photo_id=photo_id)
        db.session.add(like)
        
    db.session.commit()
    return redirect(url_for('views.photos'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route('/upload', methods=['POST'])
def upload_file():
    title = request.form.get('title')
    selected_subject = request.form.get('selectSubject')
    
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    title = request.form.get('title') 

    if not title:
        flash('Nadaj tytuł', 'error')
        return redirect(url_for('views.homePage'))



    file = request.files['file']
    
    if file.filename == '':
        flash('Brak wybranego pliku', 'error')
        return redirect(url_for('views.homePage'))
   
    if not allowed_file(file.filename):
        flash('Zły typ pliku. Dozwolonne są tylko zdjęcia', 'error')
        return redirect(url_for('views.homePage'))
    subject = request.form.get('subject')

    if not selected_subject:
        flash('Brak wybranego przedmiotu', 'error')
        return redirect(url_for('views.homePage'))

    last_upload = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.date.desc()).first()

    if last_upload and datetime.now() - last_upload.date < timedelta(days=2):
        flash('Możesz wrzucić tylko jednego posta co 2 dni.', 'error')
        return redirect(url_for('views.homePage'))

    if file:
        image_data = file.read()
        fileName = request.form.get('fileName') 
        title = request.form.get('title') 
        school_id = current_user.school_id # Convert school_id to integer
        school = School.query.get(current_user.school_id)

        
        # Create a new Photo record in the database with the image data and fileName
        photo = Photo(title=title, fileName=fileName, description='', school_id=current_user.school_id, user_id=current_user.id, image_data=image_data, school=school, credits=0, likes=[], selected_subject=selected_subject)   
        db.session.add(photo)
        db.session.commit()
        unlock = Unlock(user_id=current_user.id, photo_id=photo.id)
        db.session.add(unlock)
        db.session.commit()
        flash('Wysyłanie pliku zakończone sukcesem', 'success')
        return redirect(url_for('views.homePage'))
    
    else:
        flash('Zły format pliku', 'error')
        return redirect(request.url)





from datetime import datetime, timedelta

@views.route('/upload', methods=['POST'])
def uploadFile():
    

    last_photo = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.date.desc()).first()


    if last_photo and Photo.query.filter_by(user_id=current_user.id).filter(Photo.date > (datetime.now() - timedelta(days=2))).count() >= 5:
        flash('Możesz wrzucić tylko pięć postów co 2 dni.', 'error')
        return redirect(request.url)






from flask import send_file, Response
import io

@views.route('/download_photo/<int:photo_id>')
@login_required
def download_photo(photo_id):
    photo = Photo.query.get(photo_id)
    response = send_file(io.BytesIO(photo.image_data), mimetype='image/png', as_attachment=True, download_name='photo.png')
    return response







@views.route('/report/<int:user_id>', methods=['POST'])
@login_required
def report(user_id):
    reported_user = User.query.get(user_id)
    if not reported_user:
        flash('Nie znaleziono użytkownika.', category='error')
        return redirect(url_for('views.yourschool'))

    existing_report = Report.query.filter_by(reporter_id=current_user.id, reported_id=user_id).first()
    if existing_report:
        flash('Już zgłosiłeś tego użytkownika.', category='error')
        return redirect(url_for('views.yourschool'))

    report = Report(reporter_id=current_user.id, reported_id=user_id)
    db.session.add(report)
    db.session.commit()

    reports = Report.query.filter_by(reported_id=user_id).count()
    school_users = User.query.filter_by(school_id=reported_user.school_id).count()

    if reports >= 10 or reports / school_users >= 0.7:
        reported_user.banned = True
        db.session.commit()
    
    if user_id == current_user.id:
        flash("Nie możeesz zgłosić siebie.", "error")
        return redirect(url_for('index'))  # Replace 'index' with the appropriate route


    flash('Zgłoszono użytkownika.', category='success')
    return redirect(url_for('views.yourschool'))




@views.route('/banned')
@login_required
def banned():
    return render_template('banned.html')  # Create a banned.html template to inform the user























@views.route('/pomoc')
@views.route('/help')


def help():
    credits = None
    if current_user.is_authenticated:
        credits = current_user.credits
    return render_template('help.html', credits=credits)


# @views.route('/lodzkie')
# @login_required
# def lodzkie():
#     return render_template('schools/ŁÓDZKIE/ŁÓDZKIE.html')

# @views.route('/mazowieckie')
# @login_required
# def mazowieckie():
#     return render_template('schools/MAZOWIECKIE/MAZOWIECKIE.html')

# @views.route('/wielkopolskie')
# @login_required
# def wielkopolskie():
#     return render_template('schools/WIELKOPOLSKIE/WIELKOPOLSKIE.html')

# @views.route('/pomorskie')
# @login_required
# def pomorskie():
#     return render_template('schools/POMORSKIE/POMORSKIE.html')

# @views.route('/zachodniopomorskie')
# @login_required
# def zachodniopomorskie():
#     return render_template('schools/ZACHODNIOPOMORSKIE/ZACHODNIOPOMORSKIE.html')

# @views.route('/dolnoslaskie')
# @login_required
# def dolnoslaskie():
#     return render_template('schools/DOLNOŚLĄSKIE/DOLNOŚLĄSKIE.html')

# @views.route('/lubelskie')
# @login_required
# def lubelskie():
#     return render_template('schools/LUBELSKIE/LUBELSKIE.html')

# @views.route('/slaskie')
# @login_required
# def slaskie():
#     return render_template('schools/ŚLĄSKIE/ŚLĄSKIE.html')

# @views.route('/podlaskie')
# @login_required
# def podlaskie():
#     return render_template('schools/PODLASKIE/PODLASKIE.html')

# @views.route('/warminsko-mazurskie')
# @login_required
# def warminsko_mazurskie():
#     return render_template('schools/WARMIŃSKO-MAZURSKIE/WARMIŃSKO-MAZURSKIE.html')

# @views.route('/malopolskie')
# @login_required
# def malopolskie():
#     return render_template('schools/MAŁOPOLSKIE/MAŁOPOLSKIE.html')

# @views.route('/podkarpackie')
# @login_required
# def podkarpackie():
#     return render_template('schools/PODKARPACKIE/PODKARPACKIE.html')

# @views.route('/opolskie')
# @login_required
# def opolskie():
#     return render_template('schools/OPOLSKIE/OPOLSKIE.html')

# @views.route('/lubuskie')
# @login_required
# def lubuskie():
#     return render_template('schools/LUBUSKIE/LUBUSKIE.html')

# @views.route('/kujawsko-pomorskie')
# @login_required
# def kujawsko_pomorskie():
#     return render_template('schools/KUJAWSKO-POMORSKIE/KUJAWSKO-POMORSKIE.html')

# @views.route('/swietokrzyskie')
# @login_required
# def swietokrzyskie():
#     return render_template('schools/ŚWIĘTOKRZYSKIE/ŚWIĘTOKRZYSKIE.html')







