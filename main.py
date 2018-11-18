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

#helper functions
#precondition: 
#   query has a string that has all the proper formatting
#   parameters is a list of parameters for the query
#If don't need fetch, just pass None
def processQuery(query, parameters, fetchall=False, commit=False):
    #use cursor to interact with DB
    cursor = conn.cursor() #makes cursor object
    #print(tuple(parameters))
    cursor.execute(query, tuple(parameters))
    data = None
    if(fetchall == True):
        data = cursor.fetchall()
    elif(fetchall == False):
        data = cursor.fetchone()
    if(commit):
        conn.commit()
    cursor.close()
    return data

#checks if the user session is valid
def checkSession():
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

#Define a route to index function
@app.route('/')
def index():
    #gets result if user attempted to login
    error,success = None,None
    if(session.get('error')):
        error = session['error']
    elif(session.get('success')):
        success = session['success']
    session.clear()
    #get all public content items
    #DATE_SUB(NOW()) subtracts 24 hours from current timestamp 
    #and compare that with all the posted timestamps
    query = 'SELECT * FROM contentitem WHERE is_pub=1 AND post_time >= DATE_SUB(NOW(), INTERVAL 1 DAY) ORDER BY post_time DESC'
    result = processQuery(query,[],True)
    return render_template('index.html', error=error, success=success, items=result)

@app.route('/register', methods=['GET', 'POST'])
def registerPage():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/') #redirect to root page

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():

    username = request.form['username']
    password = request.form['password']

    #use cursor to interact with DB
    cursor = conn.cursor() #makes cursor object

    query = 'SELECT * FROM person WHERE email= %s AND password = sha2(%s,256)'
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
        query = 'INSERT INTO person VALUES (%s, sha2(%s,256), %s, %s)'
        cursor.execute(query, (username,password, firstName, lastName))
        conn.commit() #DB commits query
        cursor.close()
        success = 'You are now registered'
        session['success'] = success
        return redirect(url_for('index'))

# ==== render unique content item page
@app.route('/itemPage/item_id=<int:item_id>&item_name=<string:item_name>', methods=['GET','POST'])
def itemPage(item_id, item_name):
    checkSession()
    # gets all tagged 
    #cursor = conn.cursor()
    query = 'SELECT * FROM tag JOIN person ON (email_tagged = email) WHERE item_id=%s AND status=\'true\''
    tagItems = processQuery(query,[item_id],True)

    #cursor.execute(query, item_id)
    #tagItems = cursor.fetchall()
    #cursor.close()

    #get all ratings
    query = 'SELECT * FROM rate NATURAL JOIN person WHERE item_id=%s'
    rateItems = processQuery(query,[item_id],True)

    return render_template('contentItem.html', tagItems=tagItems, ratingItems=rateItems, item_id=item_id, item_name=item_name)



# === manages homepage
@app.route('/home', methods = ['GET', 'POST'])
def home():
    checkSession()
    #report any messages
    error,success = None,None
    if(session.get('error')):
        error = session['error']
        session.pop('error')
    elif(session.get('success')):
        success = session['success']
        session.pop('success')
    #get all viewable content (that is viewable to the user and public)
    cursor = conn.cursor()
    query = ('SELECT * FROM contentitem'
            ' LEFT OUTER JOIN (share NATURAL JOIN belong) USING (item_id) WHERE is_pub = 1 '
            'OR email=%s OR email_post=%s ORDER BY post_time DESC')
    #print(query)
    cursor.execute(query, (session['username'],session['username']))
    result = cursor.fetchall() #get all content items that are public and viewable to user
    cursor.close()

    #get the user's first name
    cursor = conn.cursor()
    query = 'SELECT fname from person WHERE email=%s'
    cursor.execute(query, session['username'])
    result2 = cursor.fetchone()
    cursor.close()

    return render_template('home.html', username=session['username'], firstName=result2['fname'], items=result, success=success)

@app.route('/createFriendGroup', methods=['GET', 'POST'])
def createFriendGroup():
    return render_template('createFriendGroup.html')

#Adds friendgroup record into DB
@app.route('/insertFriendGroup', methods=['GET','POST'])
def insertFriendGroup():
    checkSession()
    
    username = session['username']
    fg_name = request.form['fg_name']
    description = request.form['description']

    query = 'INSERT INTO friendgroup (owner_email, fg_name, description) VALUES(%s,%s,%s)'
    result = processQuery(query, [username,fg_name,description], None, True)
    success = 'FriendGroup ' + fg_name + ' created'
    session['success'] = success
    return redirect(url_for('home'))


# ============== Post Content Logic
@app.route('/postContent', methods=['GET','POST'])
def postContentPage():
    checkSession()
    #get all the friendgroups that the user belongs to
    query = 'SELECT * FROM friendgroup NATURAL JOIN belong WHERE email=%s'
    friendGroup = processQuery(query, [session['username']],True)
    return render_template('postContent.html',friendGroup=friendGroup)

#process public postings
@app.route('/processPublicContent/fg_name=<string:fg_name>', methods=['GET','POST'])
def processPublicContent(fg_name):
    checkSession()
    itemName = request.form['contentName']
    filePath = request.form['filePath']

    query = 'INSERT INTO contentitem (email_post,file_path,item_name) VALUES (%s,%s,%s)'
    result = processQuery(query, [session['username'],filePath,itemName],None,True)

    success = 'Content is now posted'
    session['success'] = success
    return redirect(url_for('home'))

#process friendgroup postings
@app.route('/processFriendGroupContent/fg_name=<string:fg_name>', methods=['GET','POST'])
def processFriendGroupContent(fg_name):
    checkSession()
    itemName = request.form['contentName']
    filePath = request.form['filePath']

    #first post the content into content table
    query = 'INSERT INTO contentitem (email_post,file_path,item_name,is_pub) VALUES (%s,%s,%s,%s)'
    result = processQuery(query, [session['username'],filePath,itemName,0],None,True)
    #find the item_id that was just inserted
    query = 'SELECT item_id FROM contentitem ORDER BY post_time DESC LIMIT 1'
    itemID = processQuery(query, [])

    #update tables to show that content is viewable to selected friendgroup
    query = 'INSERT INTO share (owner_email, fg_name, item_id) VALUES (%s, %s, %s)'
    result2 = processQuery(query, [session['username'],fg_name,itemID],None,True)

    success = 'Content is now posted'
    session['success'] = success
    return redirect(url_for('home'))


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
