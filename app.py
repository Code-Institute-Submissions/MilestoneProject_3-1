import os
from flask import Flask, render_template, jsonify, request, session, redirect
from functools import wraps
from flask_pymongo import PyMongo
from passlib.hash import pbkdf2_sha256
import uuid
import pymongo
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)

db = mongo.db


# decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    return wrap


class User:
    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return jsonify(user), 200

    def signup(self):
        print(request.form)

        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password')
        }

# Encrypt the password
        user['password'] = pbkdf2_sha256.encrypt(user['password'])
        # Check for existing email address
        if db.users.find_one({"email": user['email']}):
            return jsonify({"error": "Email address already in use"}), 400
        if db.users.insert_one(user):
            return self.start_session(user)
        return jsonify({"error": "Signup failed"}), 400

    def signout(self):
        session.clear()
        return redirect('/')

    def login(self):
        user = db.users.find_one({"email": request.form.get('email')})
        if user and pbkdf2_sha256.verify(
                                        request.form.get('password'),
                                        user['password']):
            return self.start_session(user)
        return jsonify({"error": "Invalid login credentials"}), 401


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/events')
def events():
    return render_template('events.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/signin')
def signin():
    return render_template('signin.html')


@app.route('/signout')
def signout():
    return render_template('signout.html')


@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        return User().signup()

    return render_template("signup.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)