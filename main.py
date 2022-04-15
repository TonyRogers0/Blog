import sqlalchemy.exc
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import CreatePostForm, LoginForm, RegisterForm, CommentForm, add_data, add_blog, add_comment
from flask_gravatar import Gravatar
from functools import wraps
from sqlalchemy import ForeignKey
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app, size=100, rating='g', default='wavatar', force_default=False, force_lower=False, use_ssl=False, base_url=None)




class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, ForeignKey("user.id"))
    author = relationship("User", back_populates="posts")

    comments = relationship("Comments", back_populates="parent_post")

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String, nullable=False)

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")

class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")



def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        if current_user.id != 1:
            return abort(403)

        return function(*args, **kwargs)
    return wrapper

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        password = generate_password_hash(request.form["password"])
        email = request.form["email"]

        try:

            user = add_data(User, db, name, password, email)

        except sqlalchemy.exc.IntegrityError:

            flash("User already found with this email.\nTry Logging In!")
            return redirect(url_for("login"))

        login_user(user)

        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=RegisterForm(), user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("No User found with the given email.\nKindly Sign Up for a new User")
            return redirect(url_for("register"))

        elif not check_password_hash(user.password, password):
            flash("Password doesn't match with the given email.\nPlease Try again")
            return redirect(url_for("login"))

        else:
            login_user(user)
            return redirect(url_for("get_all_posts"))


    return render_template("login.html", form=LoginForm(), user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Login to post your comment")
            return redirect(url_for("login"))

        text = request.form["body"]
        add_comment(Comments, db, text, current_user.id, post_id)



    requested_post = BlogPost.query.get(post_id)
    comments = Comments.query.all()
    return render_template("post.html", post=requested_post, user=current_user, form=CommentForm(), comments=comments, gravatar=gravatar)


@app.route("/about")
def about():
    return render_template("about.html", user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", user=current_user)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()

    if request.method == "POST":
        add_blog(BlogPost, db, title=form.title.data, subtitle=form.subtitle.data, body=form.body.data, img_url=form.img_url.data, author_id=current_user.id, date=date.today().strftime("%B %d, %Y"))



        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", 'POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
