from flask import Flask, request, redirect, render_template, url_for, session, flash
from flask_wtf import FlaskForm
from flask_cors import CORS
import string
import random
import os
from dotenv import load_dotenv
from flask_mysqldb import MySQL
import bcrypt
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError

app = Flask(__name__)
CORS(app)
load_dotenv()

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.secret_key = os.getenv('SECRET_KEY')

mysql = MySQL(app)

# class generateURL:

def generate_short_url(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route("/shorten", methods=["GET", "POST"])
def index():
    if 'user_id' not in session:
        flash('You must be logged in to view that page.')
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT short_url, counter FROM url_map WHERE user_id = %s", [session['user_id']])
    short_codes = cur.fetchall()
    if request.method == "POST":
        original_url = request.form['original_url']
        alias = request.form['alias']
        counter = 0
        user_id = session['user_id']
        result = cur.execute("SELECT * FROM url_map WHERE short_url = %s", [alias])
        if alias:    
            if result > 0:
                flash(f"Alias {alias} already in use!")
                return redirect(url_for('index'))
            else:
                cur.execute("INSERT INTO url_map(short_url, original_url, user_id, counter) VALUES(%s, %s, %s, %s)", (alias, original_url, user_id, counter))
                mysql.connection.commit()
                return redirect(url_for('show_url', short_url=alias))
        
        short_url = generate_short_url()
        result = cur.execute("SELECT * FROM url_map WHERE short_url = %s", [short_url])
        while result > 0:
            short_url = generate_short_url()
            result = cur.execute("SELECT * FROM url_map WHERE short_url = %s", [short_url])
        cur.execute("INSERT INTO url_map(short_url, original_url, user_id, counter) VALUES(%s, %s, %s, %s)", (short_url, original_url, user_id, counter))
        mysql.connection.commit()
        return redirect(url_for('show_url', short_url=short_url))
    
    return render_template("index.html", short_codes=short_codes)

@app.route("/<short_url>")
def redirect_urls(short_url):
    cur = mysql.connection.cursor()
    cur.execute("SELECT original_url, counter FROM url_map WHERE short_url = %s", [short_url])
    result = cur.fetchone()
    if result:
        original_url, counter = result
        counter += 1
        cur.execute("UPDATE url_map SET counter = %s WHERE short_url = %s", (counter, short_url))
        mysql.connection.commit()

        return redirect(original_url)
    else:
       flash("URL not Found!")
       return redirect(url_for('index'))
    
@app.route("/show_url/<short_url>")
def show_url(short_url):
    return render_template("show_url.html", short_url=request.url_root + short_url)

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

@app.route('/',methods=['GET','POST'])
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
            session['user_name'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html',form=form)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)