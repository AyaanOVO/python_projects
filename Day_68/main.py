from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

login_manager = LoginManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'My-top-secret-key-goes-here'
login_manager.init_app(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy()
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE TABLE IN DB
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        all_data_from_db = User.query.all()
        for item in all_data_from_db:
            if item.email == email:
                error = "You already sign up please log in!"
                return render_template("secrets.html", error=error)

        password_get = request.form['password']
        password_hashed = generate_password_hash(password_get, method="pbkdf2:sha256", salt_length=8)
        new_data = User(email=email, password=password_hashed, name=name)
        login_user(new_data)
        print('reg',new_data)
        db.session.add(new_data)
        db.session.commit()

        return render_template('secrets.html', name=name)

    return render_template("register.html", error=error)


@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user_email = request.form.get('email')
        user_password = request.form.get('password')
        all_data_in_db = User.query.all()
        for users in all_data_in_db:
            if users.email != user_email:
                error = "Email does not exit please try again"
                break
            elif not check_password_hash(users.password, user_password):
                error = "Password was incorrect"
                break
            elif users.email == user_email and check_password_hash(users.password, user_password):
                login_user(users)
                print('in',users)
                return redirect(url_for('secrets'))
    return render_template("login.html", error=error)


@app.route('/secrets')
@login_required
def secrets():
    return render_template("secrets.html", name=current_user.name)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/download')
@login_required
def download():
    return send_from_directory('static', path="files/cheat_sheet.pdf")


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
