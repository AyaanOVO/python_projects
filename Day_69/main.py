import flask
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from forms import RegisterForm, CreatePostForm, LoginForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    user_post = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship("Comment", backref='blogpost')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship('BlogPost', backref='user')
    comment = db.relationship('Comment', backref='user')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'))
    user_post = db.Column(db.Integer, db.ForeignKey('user.id'))


with app.app_context():
    db.create_all()


def check_if_authorized(current_user):
    if current_user.is_authenticated:
        if int(current_user.get_id()) != 1:
            return flask.abort(403)
    else:
        return flask.abort(403)


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    error = None
    if form.validate_on_submit():
        all_data_in_db_user = User.query.all()
        flag = True
        for data in all_data_in_db_user:
            if data.email == form.email.data:
                flag = False
                break

        if not flag:
            error = "Email is already exit please log in!"
            return render_template("register.html", form=form, error=error)
        else:
            hashed = generate_password_hash(password=request.form['password'], method="pbkdf2:sha256", salt_length=8)
            new_user = User(name=request.form['name'], email=request.form['email'], password=hashed)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = hashed_password = user = None
    form = LoginForm()
    if form.validate_on_submit():
        flag = False
        all_data_in_db_user = User.query.all()
        for data in all_data_in_db_user:
            if data.email == form.email.data:
                user = data
                hashed_password = data.password
                flag = True
                break

        if not flag:
            error = "Email does not exit, please try again"
            return render_template("login.html", form=form, error=error)
        else:
            if check_password_hash(password=form.password.data, pwhash=hashed_password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                error = "Password was incorrect"
                return render_template("login.html", form=form, error=error)
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()

    return render_template("index.html", all_posts=posts, post_length=len(posts))


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    all_user_that_commented = Comment.query.filter_by(post_id=post_id).all()
    formcomment = CommentForm()
    if request.method == "POST":
        error = "Please first log in then you can comment out"
        if current_user.is_authenticated:
            comment = formcomment.comment_ckeditor.data
            post_id_that_comment = BlogPost.query.filter_by(id=post_id).first()
            adding_comment = Comment(text=comment, user=current_user, blogpost=post_id_that_comment)
            db.session.add(adding_comment)
            db.session.commit()

        else:
            return redirect(url_for('login'))

    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post, formcomment=formcomment, post_id=post_id,
                           all_user_that_commented=all_user_that_commented)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    check_if_authorized(current_user)
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user.name,
            date=date.today().strftime("%B %d, %Y"),
            user=current_user
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    check_if_authorized(current_user)
    post = db.get_or_404(BlogPost, post_id)
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
        post.author = current_user.name
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    check_if_authorized(current_user)
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
