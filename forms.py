from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField, PasswordField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired,email, URL, Length
from flask_ckeditor import CKEditor, CKEditorField

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), email()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')



ckeditor = CKEditor()
class CreatePostForm(FlaskForm):
    title = StringField('Blog Post Title', validators=[DataRequired()])
    subtitle = StringField('Blog Post Subtitle', validators=[DataRequired()])
    body = CKEditorField('Blog Content', validators=[DataRequired()])
    #author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired(), Length(max=10)])
    email = StringField('Email Address', validators=[DataRequired(), email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')

class CommentForm(FlaskForm):
    comment = CKEditorField(validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

class ProfileForm(FlaskForm):
    image = FileField('Change Picture', validators=[FileRequired(), FileAllowed(['jpg','png'],'Images only!')])
    submit = SubmitField('Submit')