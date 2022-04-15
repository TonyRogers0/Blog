from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LogIn")


class CommentForm(FlaskForm):
    body = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


def add_data(obj, db, name, password, email):
    new_user = obj(name=name, password=password, email=email)
    db.session.add(new_user)
    db.session.commit()

    return new_user

def add_blog(obj, db, title, subtitle, body, date, img_url, author_id):
    post = obj(title=title, subtitle=subtitle, body=body, date=date, img_url=img_url, author_id=author_id)
    db.session.add(post)
    db.session.commit()

def add_comment(obj, db, text, author_id, id):
    comment = obj(comment=text, author_id=author_id, post_id=id)
    db.session.add(comment)
    db.session.commit()
