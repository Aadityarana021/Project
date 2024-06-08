from flask import Flask, request, jsonify, session, redirect, url_for, flash, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt 
import mysql.connector

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mydatabase'
app.secret_key = 'your_secret_key_here'

# mysql = MySQL(app)

mydb = mysql.connector.connect(
        host="127.0.0.2",
        user="root",
        password="",
        database="mydatabase"
        )

cursor = mydb.cursor()

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self,field):

        mydb = mysql.connector.connect(
        host="127.0.0.2",
        user="root",
        password="",
        database="mydatabase"
        )

        cursor = mydb.cursor()

        # cursor = mysql.connect.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')

class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())



        mydb = mysql.connector.connect(
        host="127.0.0.2",
        user="root",
        password="",
        database="mydatabase"
        )

        cursor = mydb.cursor()

        


        # store data into database 
        # cursor = mysql.connect.cursor()
        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",(name,email,hashed_password))
        mydb.commit()

        print("Data inserted successfully!")

        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():


    mydb = mysql.connector.connect(
        host="127.0.0.2",
        user="root",
        password="",
        database="mydatabase"
        )

    cursor = mydb.cursor()


    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # cursor = mysql.connect.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html',form=form)

@app.route('/dashboard')
def dashboard():

    mydb = mysql.connector.connect(
        host="127.0.0.2",
        user="root",
        password="",
        database="mydatabase"
        )

    cursor = mydb.cursor()

    if 'user_id' in session:
        user_id = session['user_id']

        # cursor = mysql.connect.cursor()
        cursor.execute("SELECT * FROM users where id=%s",(user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            return render_template('dashboard.html',user=user)
            
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)