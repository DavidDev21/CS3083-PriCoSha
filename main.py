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
    #report any messages
    error,success = None,None
    if(session.get('error')):
        error = session['error']
        session.pop('error')
    elif(session.get('success')):
        success = session['success']
        session.pop('success')
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

    return render_template('contentItem.html', success=success,tagItems=tagItems, ratingItems=rateItems, item_id=item_id, item_name=item_name)



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

    fg_name = request.form['fg_name']
    description = request.form['description']

    #Insert friendgroup details into table
    query = 'INSERT INTO friendgroup (owner_email, fg_name, description) VALUES(%s,%s,%s)'
    result = processQuery(query, [session['username'],fg_name,description], None, True)

    #the owner is automatically belong into the new friendgroup
    query = 'INSERT INTO belong (email, owner_email, fg_name) VALUES(%s,%s,%s)'
    result2 = processQuery(query,[session['username'],session['username'],fg_name], None, True)

    success = 'FriendGroup, ' + fg_name + ', created'
    session['success'] = success
    return redirect(url_for('home'))


# ============== Post Content Logic
@app.route('/postContent', methods=['GET','POST'])
def postContentPage():
    checkSession()
    #get all the friendgroups that the user belongs to
    #friendgroup has the description information
    query = 'SELECT * FROM friendgroup NATURAL JOIN belong WHERE email=%s'
    friendGroup = processQuery(query, [session['username']],True)
    return render_template('postContent.html',friendGroup=friendGroup)

#process postings
@app.route('/processContent/fg_name=<string:fg_name>&fg_owner=<string:fg_owner>', methods=['GET','POST'])
def processContent(fg_name,fg_owner):
    print('I am in processContent()')
    checkSession()
    # print(request.form.get('contentName'))
    # print(request.form.get('filePath'))
    # print(request.form)
    itemName = request.form['contentName']
    filePath = request.form['filePath']
    
    if(fg_name == 'public'):
        query = 'INSERT INTO contentitem (email_post,file_path,item_name) VALUES (%s,%s,%s)'
        result = processQuery(query, [session['username'],filePath,itemName],None,True)
    else:
        #first post the content into content table
        query = 'INSERT INTO contentitem (email_post,file_path,item_name,is_pub) VALUES (%s,%s,%s,%s)'
        result = processQuery(query, [session['username'],filePath,itemName,0],None,True)
        #find the item_id that was just inserted
        query = 'SELECT item_id FROM contentitem ORDER BY post_time DESC LIMIT 1'
        itemID = processQuery(query, [])

        # #get the owner of the friendgroup that you want to share to
        # query = 'SELECT * FROM belong WHERE email=%s AND fg_name=%s'
        # friendGroupInfo = processQuery(query, [session['username'],fg_name])

        #update tables to show that content is viewable to selected friendgroup
        query = 'INSERT INTO share (owner_email, fg_name, item_id) VALUES (%s, %s, %s)'

        result2 = processQuery(query, [fg_owner,fg_name,itemID['item_id']],None,True)
    
    success = 'Content is now posted'
    session['success'] = success
    return redirect(url_for('home'))

# ==== Tag person
@app.route('/tagPerson/<int:item_id><string:item_name>', methods=['GET', 'POST'])
def tagPerson(item_id,item_name):
    checkSession()

    tagEmail = request.form['tagEmail']
    
    #self tag
    if(tagEmail == session['username']):
        query = 'INSERT INTO tag (email_tagged,email_tagger,item_id,status) VALUES (%s,%s,%s,%s)'
        result = processQuery(query,[tagEmail,tagEmail,item_id,'true'])
        session['success'] = tagEmail + ' is now tagged'
        return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))
    
    #see if the content item is actually visible to the tagPerson
    query = ('SELECT * FROM contentitem'
        ' LEFT OUTER JOIN (share NATURAL JOIN belong) USING (item_id) WHERE item_id=%s AND (is_pub = 1 '
        'OR email=%s OR email_post=%s)')
    item = processQuery(query,[item_id,tagEmail,tagEmail])
    
    #the item is visible to the tagPerson
    if(len(item)):
        query = 'INSERT INTO tag (email_tagged, email_tagger, item_id) VALUES (%s, %s, %s)'
        result = processQuery(query, [tagEmail,session['username'],item_id],None,True)
        session['success'] = tagEmail + ' is now tagged'
        return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))
    
    #the item is not visibile to tagPerson
    session['error'] = 'Can not tag, ' + tagEmail + ' , on this content item'
    return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))

# ==== tags
@app.route('/manageTags')
def manageTagPage():
    checkSession()

    query = 'SELECT * FROM tag NATURAL JOIN contentitem WHERE email_tagged=%s AND status=\'false\''
    tags = processQuery(query,[session['username']],True)
    return render_template('manageTags.html', items=tags)

@app.route('/tagActions/tagger=<string:tagger>&item=<int:item_id>', methods=['GET','POST'])
def tagActions(tagger, item_id):
    checkSession()

    action = request.form['action']

    #change status of tag
    if(action == 'accept'):
        query = 'UPDATE tag SET status=\'true\' WHERE email_tagged=%s AND email_tagger=%s AND item_id=%s'
        result = processQuery(query, [session['username'], tagger, item_id], None, True)
        session['success'] = 'You have accepted the tag from ' + tagger
        return redirect(url_for('home'))
    #remove tag from tag table
    elif(action == 'decline'):
        query = 'DELETE FROM tag WHERE email_tagged=%s AND email_tagger=%s AND item_id=%s'
        result = processQuery(query, [session['username'], tagger, item_id], None, True)
        session['success'] = 'The tag from ' + tagger + ' has been removed'
        return redirect(url_for('home'))

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
