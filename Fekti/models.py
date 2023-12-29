from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    fileName = db.Column(db.String(255))
    description = db.Column(db.String(1000))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    selected_subject = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_data = db.Column(db.LargeBinary)
    likes = db.relationship('Like', backref='photo', lazy='dynamic')
    school = db.relationship('School', backref='photos')  # Add this line
    credits = db.Column(db.Integer, default=2)
    likes_count = db.Column(db.Integer, default=0)
    removed = db.Column(db.Boolean, default=False)

       


    def __init__(self, title, fileName, description, school_id, user_id, image_data, school, credits, likes, selected_subject):
        self.title = title
        self.fileName = fileName
        self.description = description
        self.school_id = school_id
        self.user_id = user_id
        self.image_data = image_data
        self.school = school
        self.credits = credits
        self.likes = likes
        self.selected_subject = selected_subject


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    username = db.Column(db.String(150), unique=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))  # Add this line
    photos = db.relationship('Photo')
    credits = db.Column(db.Integer, default=2)
    unlocked_photos = db.relationship('Unlock', backref='user', lazy=True)
    last_credit_update = db.Column(db.DateTime(timezone=True), default=func.now())
    confirmed = db.Column(db.Boolean, default=False)
    banned = db.Column(db.Boolean, default=False)  # Add this line
    vote = db.Column(db.Boolean, default=True,)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, photo_id, user_id):
        self.photo_id = photo_id
        self.user_id = user_id


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    users = db.relationship('User', backref='school', lazy=True)
    def get_mainusers(self):
        return User.query.filter_by(school_id=self.id).all()


class Unlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class PhotoFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback = db.Column(db.Boolean, nullable=False)  # True for like, False for dislike
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())


class NeededFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    isRated = db.Column(db.Boolean, default=False)