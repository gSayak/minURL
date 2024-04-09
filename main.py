from flask import Flask, request, jsonify, redirect, render_template, url_for, session, flash
from flask_wtf import FlaskForm
from flask_cors import CORS
import string
import random
from flask_mysqldb import MySQL
import bcrypt
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError

app = Flask(__name__)
CORS(app)

shortened_urls = {}
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'min_url'
app.secret_key = 'abcdefg'

mysql = MySQL(app)

def generate_short_url(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = request.form['original_url']
        alias = request.form['alias']
        
        if alias:  # If alias is provided
            if alias in shortened_urls:
                return f"Alias '{alias}' is already in use."
            else:
                shortened_urls[alias] = original_url
                return f"Shortened URL: {request.url_root}{alias}"
        
        short_url = generate_short_url()
        while short_url in shortened_urls:
            short_url = generate_short_url()
        
        shortened_urls[short_url] = original_url
        return f"Shortened URL: {request.url_root}{short_url}"
    
    return render_template("index.html")

@app.route("/<short_url>")
def redirect_urls(short_url):
    original_url = shortened_urls.get(short_url)
    if original_url:
        return redirect(original_url)
    else:
        return "URL not found", 404
    

#handling the Register section

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",(name,email,hashed_password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html',form=form)

#handling the Login Form

class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html',form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)