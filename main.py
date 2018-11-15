#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='prichocho',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to index function
@app.route('/')
def index():
    error,success = None,None
    if(session.get('error')):
        error = session['error']
    elif(session.get('success')):
        success = session['success']
    session.clear()
    return render_template('index.html', error=error, success=success)

@app.route('/register', methods=['GET', 'POST'])
def registerPage():
    return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():

    username = request.form['username']
    password = request.form['password']

    #use cursor to interact with DB
    cursor = conn.cursor() #makes cursor object

    query = 'SELECT * FROM person WHERE email= %s AND password = %s'
    cursor.execute(query, (username,password))

    data = cursor.fetchone()

    cursor.close()
    error = None
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login. Check username and password'
        session['error'] = error #pass the error along
        return redirect(url_for('index'))


@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    error = None
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['first_name']
    lastName = request.form['last_name']

    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE email=%s'
    cursor.execute(query, username)

    result = cursor.fetchone()

    #User already exists
    if(result):
        error='That username already exists. Please use a different email.'
        return render_template('register.html', error=error)
    else:            
        #User does not exists, Insert User into person
        query = 'INSERT INTO person VALUES (%s, %s, %s, %s)'
        cursor.execute(query, (username,password, firstName, lastName))
        conn.commit() #DB commits query
        cursor.close()
        success = 'You are now registered'
        session['success'] = success
        return redirect(url_for('index'))

@app.route('/home', methods = ['GET', 'POST'])
def home():
    cursor = conn.cursor()
    query = 'SELECT * from person WHERE email=%s'
    cursor.execute(query, session['username'])
    result = cursor.fetchone()
    print(result)
    cursor.close()
    return render_template('home.html', username=session['username'], firstName=result['fname'])

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
