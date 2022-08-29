import uuid

from flask import Flask, render_template, redirect, url_for, request, flash, abort, escape
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_gravatar import Gravatar
from sqlalchemy.orm import relationship
import requests
import os
import api,forms,functions
from datetime import date
from functools import wraps
from werkzeug.utils import secure_filename


import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager, login_user, current_user, logout_user,login_required

from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    Bootstrap(app)
    app.secret_key= os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

app=create_app()
db = SQLAlchemy(app)
forms.ckeditor.init_app(app)

UPLOAD_FOLDER = 'static/img/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


login_manager = LoginManager()
login_manager.init_app(app)


# Creating admin privileges
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# TABLES ---------------------------------------------------------------------------------------------------------------
class Users(UserMixin,db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False )
    name = db.Column(db.String(250), nullable=False)
    profile_pic = db.Column(db.String(250), nullable=True, default='avatar.png')

    posts = relationship('BlogPost', back_populates = 'author')
    comments = relationship('Comment', back_populates = 'author')
    likes = relationship('Like', back_populates = 'author')
    dislikes = relationship('Dislike', back_populates='author')
class BlogPost(db.Model):
    __tablename__='blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=False, nullable=False)
    subtitle = db.Column(db.String(250), default='None', nullable=True )
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), default='None')

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship('Users', back_populates='posts')

    comments = relationship('Comment', back_populates='post')


class Comment(db.Model):
    __tablename__= 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship('Users', back_populates='comments')

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    post = relationship('BlogPost', back_populates='comments')

    likes = relationship('Like', back_populates='comments')
    dislikes = relationship('Dislike', back_populates='comments')


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship('Users', back_populates='likes')
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"))
    comments = relationship('Comment', back_populates='likes')

class Dislike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship('Users', back_populates='dislikes')
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"))
    comments = relationship('Comment', back_populates='dislikes')


#db.create_all()


# NEWS ROUTES___________________________________________________________________________________________________________
@app.route('/')
def home():
    if current_user.is_authenticated:
        if not current_user.profile_pic:
            current_user.profile_pic='avatar.png'
            db.session.commit()
    return render_template('index.html',posts=api.posts, logged_in = current_user.is_authenticated)

# FORUM ROUTES__________________________________________________________________________________________________________
@app.route('/forum')
def forum():
    posts = BlogPost.query.all()
    return render_template('forum.html',posts=posts, logged_in = current_user.is_authenticated)

@app.route('/forum_post/<int:id>', methods=['GET','POST'])
def forum_post(id):
    requested_post = BlogPost.query.get(id)
    comments = Comment.query.filter_by(post_id=id).all()
    comment_form = forms.CommentForm()
    if comment_form.validate_on_submit():
        new_comment = Comment(text= comment_form.comment.data,
                              post_id=id,
                              author_id=current_user.id,
                              date=datetime.datetime.now().strftime("%H:%M, %d %b, %Y"))
        db.session.add(new_comment)
        db.session.commit()
    comments = Comment.query.filter_by(post_id=id).all()
    return render_template('post.html', post = requested_post,is_forum=True,
                           comments = comments, logged_in = current_user.is_authenticated,
                           form=comment_form)

@app.route('/new_post', methods=['GET','POST'])
def make_post():
    create_post_form = forms.CreatePostForm()
    if create_post_form.validate_on_submit():
        new_post = BlogPost(title=create_post_form.title.data,
                            subtitle=create_post_form.subtitle.data,
                            date = date.today().strftime("%B %d, %Y"),
                            body=create_post_form.body.data,
                            author_id=current_user.id,
                            img_url=create_post_form.img_url.data)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('forum'))
    return render_template('make_post.html',form=create_post_form, is_edit = False, logged_in = current_user.is_authenticated)

@app.route('/edit_post/<int:id>', methods=['GET','POST'])
def edit_post(id):
    post_to_edit = BlogPost.query.get(id)
    edit_post_form = forms.CreatePostForm(
        title=post_to_edit.title,
        subtitle=post_to_edit.subtitle,
        body= post_to_edit.body,
        #author=post_to_edit.author.name,
        img_url=post_to_edit.img_url
    )

    if edit_post_form.validate_on_submit():
        post_to_edit.title = edit_post_form.title.data
        post_to_edit.subtitle = edit_post_form.subtitle.data
        post_to_edit.body = edit_post_form.body.data
        #post_to_edit.author.name = edit_post_form.author.data
        post_to_edit.img_url = edit_post_form.img_url.data
        db.session.commit()
        return redirect(url_for('forum_post', id=id))
    return render_template('make_post.html', edit_form=edit_post_form, is_edit=True, logged_in = current_user.is_authenticated)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = BlogPost.query.get(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('forum'))



# Comment routes________________________________________________________________________________________________________
@app.route('/likes/<int:id>') ## AUTHENTICATE THE USER -> OVA DA SE DOVRSI
def likes(id):
    comment_to_update = Comment.query.get(id)
    if current_user.is_authenticated:
        already_liked = Like.query.filter_by(author_id=current_user.id,comment_id=id).first()
        already_disliked = Dislike.query.filter_by(author_id=current_user.id,comment_id=id).first()
        if already_disliked:
            db.session.delete(already_disliked)
            new_like = Like(author_id = current_user.id,
                            comment_id = id)
            db.session.add(new_like)
            db.session.commit()
        else:
            if not already_liked:
                new_like = Like(author_id=current_user.id,
                                comment_id=id)
                db.session.add(new_like)
                db.session.commit()
            else:
                db.session.delete(already_liked)
                db.session.commit()
    else:
        flash("Please log in to be able to react to posts!", "error")
        return redirect(url_for('login'))
    return redirect(url_for('forum_post',id=comment_to_update.post_id))

@app.route('/dislikes/<int:id>')
def dislikes(id):
    comment_to_update = Comment.query.get(id)
    if current_user.is_authenticated:
        already_disliked = Dislike.query.filter_by(author_id=current_user.id,comment_id=id).first()
        already_liked  = Like.query.filter_by(author_id=current_user.id,comment_id=id).first()
        # If the comment was liked by the user and now is being disliked by the same user.
        if already_liked:
            db.session.delete(already_liked)
            new_dislike = Dislike(author_id=current_user.id,
                                  comment_id=id)
            db.session.add(new_dislike)
            db.session.commit()
        else:
            if not already_disliked:
                new_dislike = Dislike(author_id=current_user.id,
                                comment_id=id)
                db.session.add(new_dislike)
                db.session.commit()
            else:
                db.session.delete(already_disliked)
                db.session.commit()
    else:
        flash("Please log in to be able to react to posts!", "error")
        return redirect(url_for('login'))
    return redirect(url_for('forum_post', id=comment_to_update.post_id))

@app.route('/delete_comment/<int:id>')
def delete_comment(id):
    comment_to_delete = Comment.query.get(id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('forum_post', id = comment_to_delete.post_id))

# Information routes____________________________________________________________________________________________________


@app.route('/contact', methods=['GET','POST'])
def contact():
    contact_form = forms.ContactForm()
    if contact_form.validate_on_submit():
        functions.send_email(name=contact_form.name.data,
                             email=contact_form.email.data,
                             phone_number=contact_form.phone_number.data,
                             message=contact_form.message.data)
        return redirect(url_for('contact'))
    return render_template('contact.html', form=contact_form, logged_in = current_user.is_authenticated)

@app.route('/profile_page', methods=['GET','POST'])
@login_required
def profile_page():
    profile_form = forms.ProfileForm()
    user = Users.query.get(current_user.id)
    posts_by_user = db.session.query(BlogPost).filter_by(author_id=current_user.id).all()
    if profile_form.validate_on_submit():
        profile_pic = profile_form.image.data
        print(profile_pic)
        # Grab image name
        filename = secure_filename(profile_pic.filename)
        # Set UUID
        pic_name = str(uuid.uuid1()) + "_" + filename

        # Import the name into db
        user.profile_pic = pic_name

        try:
            db.session.commit()
            # Save the image
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            return redirect(url_for('home'))
        except:
            flash('Problem with the image!')
            return render_template('profile_page.html', form=profile_form,
                                   logged_in = current_user.is_authenticated, number=len(posts_by_user))
    return render_template('profile_page.html', form=profile_form,
                           logged_in = current_user.is_authenticated, number=len(posts_by_user))



# Authentication routes_________________________________________________________________________________________________
@app.route('/register',methods=['GET','POST'])
def register():
    # Preventing the 'register route' for authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    register_form = forms.RegisterForm()
    if register_form.validate_on_submit():
        # If user exists
        if Users.query.filter_by(email=register_form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password = register_form.password.data,
                                                         method = 'pbkdf2:sha256',
                                                         salt_length = 8)



        if check_password_hash(hashed_password, register_form.confirm_password.data):
            new_user = Users(name = register_form.name.data,
                             email = register_form.email.data,
                             password = hashed_password
                             )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            flash("Passwords do not match. Try again")

    return render_template('register.html', form=register_form)

@app.route('/login', methods=['GET','POST'])
def login():
    # Preventing the 'login route' for authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    login_form=forms.LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user = Users.query.filter_by(email=email).first()

        # If user is not registered
        if not user:
            flash("That email does not exist. Please try again")
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=login_form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='localhost',debug=True, port=5000)

