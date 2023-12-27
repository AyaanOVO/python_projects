from flask import Flask
from faker import Faker
from flask_sqlalchemy import SQLAlchemy
import random
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///practice.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Father
class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)
    pets = db.relationship("Pet", backref="owner")


# Child
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    age = db.Column(db.String)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'))


with app.app_context():
    db.create_all()


@app.route('/')
def home_page():
    return "<h1>Hey</h1>"


if __name__ == "__main__":
    app.run(debug=True)