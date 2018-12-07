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

#checks if the user session is valid
def checkSession():
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

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
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
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

    #get filePath
    query = 'SELECT file_path FROM contentitem WHERE item_id=%s'
    filePath = processQuery(query, [item_id])['file_path']

    username = session['username']
    return render_template('contentItem.html', filePath=filePath, success=success,error=error, tagItems=tagItems, ratingItems=rateItems, item_id=item_id, item_name=item_name, username=username)



# === manages homepage
@app.route('/home', methods = ['GET', 'POST'])
def home():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
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
    # don't need email_post since you belong into a group when you post
    query = ('SELECT * FROM contentitem'
            ' LEFT OUTER JOIN (share NATURAL JOIN belong) USING (item_id) WHERE is_pub = 1 '
            'OR email=%s ORDER BY post_time DESC')
    #print(query)
    cursor.execute(query, (session['username']))
    result = cursor.fetchall() #get all content items that are public and viewable to user
    cursor.close()

    #get the user's first name
    cursor = conn.cursor()
    query = 'SELECT fname from person WHERE email=%s'
    cursor.execute(query, session['username'])
    result2 = cursor.fetchone()
    cursor.close()

    return render_template('home.html', username=session['username'], firstName=result2['fname'], items=result, success=success, error=error)

@app.route('/createFriendGroup', methods=['GET', 'POST'])
def createFriendGroup():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
    return render_template('createFriendGroup.html')

#Adds friendgroup record into DB
@app.route('/insertFriendGroup', methods=['GET','POST'])
def insertFriendGroup():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

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

@app.route('/leaveFriendGroup')
def leaveFriendGroupPage():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
    query = 'SELECT * FROM belong NATURAL JOIN friendgroup WHERE email=%s AND owner_email != %s'
    result = processQuery(query,[session['username'], session['username']],True)
    return render_template('leaveFriendGroup.html' , items=result)

@app.route('/leaveGroupAction/fg_name=<string:fg_name>&fg_owner=<string:fg_owner>', methods=['GET','POST'])
def leaveGroupAction(fg_name, fg_owner):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
    #User shouldn't leave their own friendgroup. (may in the future)
    if(fg_owner == session['username']):
        session['error'] = 'Owner shouldn\'t leave their own group'
        return redirect(url_for('home'))
    
    #delete user from belong table
    query = 'DELETE FROM belong WHERE email=%s AND owner_email=%s AND fg_name=%s'
    result = processQuery(query, [session['username'],fg_owner, fg_name],None, True)
    session['success'] = 'You are no longer part of: ' + fg_name
    return redirect(url_for('home'))

@app.route('/kickFriend')
def kickFriend():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

    query = 'SELECT fname,lname,email,fg_name,owner_email FROM belong NATURAL JOIN friendgroup NATURAL JOIN person WHERE email!=%s AND owner_email=%s'
    result = processQuery(query,[session['username'],session['username']],True)
    if(result):
        return render_template('kickFriend.html', items=result)

    session['error'] = 'You do not own any friendgroups'
    return redirect(url_for('home'))

@app.route('/processKick/email=<string:email>&fg_name=<string:fg_name>', methods=['GET','POST'])
def processKick(email, fg_name):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

    query = 'DELETE FROM belong WHERE email=%s AND owner_email=%s AND fg_name=%s'
    result = processQuery(query,[email,session['username'],fg_name],None, True)

    session['success'] = email + ' has been kicked out of ' + fg_name
    return redirect(url_for('home'))

# ============== Post Content Logic
@app.route('/postContent', methods=['GET','POST'])
def postContentPage():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
    #get all the friendgroups that the user belongs to
    #friendgroup has the description information
    query = 'SELECT * FROM friendgroup NATURAL JOIN belong WHERE email=%s'
    friendGroup = processQuery(query, [session['username']],True)
    return render_template('postContent.html',friendGroup=friendGroup)

#process postings
@app.route('/processContent/fg_name=<string:fg_name>&fg_owner=<string:fg_owner>', methods=['GET','POST'])
def processContent(fg_name,fg_owner):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
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
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

    tagEmail = request.form['tagEmail']
    
    #check if the email is valid
    query = 'SELECT email FROM person WHERE email=%s'
    valid = processQuery(query,[tagEmail])

    if(valid == None):
        session['error'] = 'Invalid email'
        return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))

    #check if the email already has a tag request
    query = 'SELECT email_tagged FROM tag WHERE email_tagger=%s AND email_tagged=%s AND item_id=%s'
    existTag = processQuery(query,[session['username'],tagEmail,item_id])

    if(existTag):
        session['error'] = tagEmail + ' already is tagged / has a pending tag request from you'
        return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))

    #self tag
    if(tagEmail == session['username']):
        query = 'INSERT INTO tag (email_tagged,email_tagger,item_id,status) VALUES (%s,%s,%s,%s)'
        result = processQuery(query,[tagEmail,tagEmail,item_id,'true'])
        session['success'] = 'Self-Tag successful!'
        return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))
    
    #see if the content item is actually visible to the tagPerson
    query = ('SELECT * FROM contentitem'
        ' LEFT OUTER JOIN (share NATURAL JOIN belong) USING (item_id) WHERE item_id=%s AND (is_pub = 1 '
        'OR email=%s)')
    item = processQuery(query,[item_id,tagEmail])
    
    #the item is visible to the tagPerson
    if(item):
        query = 'INSERT INTO tag (email_tagged, email_tagger, item_id) VALUES (%s, %s, %s)'
        result = processQuery(query, [tagEmail,session['username'],item_id],None,True)
        session['success'] = tagEmail + ' has been sent a tag request'
        return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))
    
    #the item is not visibile to tagPerson
    session['error'] = 'Can not tag, ' + tagEmail + ' , on this content item'
    return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))

#== process rating
@app.route('/rateItem/<int:item_id><string:item_name>', methods=['GET','POST'])
def rateItem(item_id, item_name):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

    rating = request.form['starValue']
    query = 'SELECT * FROM rate WHERE email=%s AND item_id=%s'
    oldRating = processQuery(query, [session['username'], item_id])

    if(oldRating):
        query = 'UPDATE rate SET emoji=%s, rate_time=CURRENT_TIMESTAMP WHERE email=%s AND item_id=%s'
        result = processQuery(query, [rating,session['username'], item_id], None, True)
    else:
        query = 'INSERT INTO rate(email, item_id, emoji) VALUES (%s, %s, %s)'
        result = processQuery(query, [session['username'], item_id, rating], None, True)

    return redirect(url_for('itemPage', item_id=item_id, item_name=item_name))

# ==== tags
@app.route('/manageTags')
def manageTagPage():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

    query = 'SELECT * FROM tag NATURAL JOIN contentitem WHERE email_tagged=%s AND status=\'false\''
    tags = processQuery(query,[session['username']],True)
    return render_template('manageTags.html', items=tags)

@app.route('/tagActions/tagger=<string:tagger>&item=<int:item_id>', methods=['GET','POST'])
def tagActions(tagger, item_id):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

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



#== manages add friend to group
#Note: the current user is the owner
@app.route('/addFriend', methods=['GET','POST'])
def addFriend():
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
    #get all the friendgroups that the user owns
    query = 'SELECT * FROM friendgroup WHERE owner_email=%s'
    friendGroup = processQuery(query, [session['username']],True)
    return render_template('addFriend.html', friendGroup=friendGroup)

#addFriendConfirmation assumes the user is already the owner of the friendgroup
@app.route('/addFriendConfirmation/fg_name=<string:fg_name>', methods=['GET','POST'])
def addFriendConfirmation(fg_name):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))

    firstName = request.form['firstName']
    lastName = request.form['lastName']

    # Gets anyone with the matching name minus person who may already be part of the fg
    query = ('SELECT fname,lname,email FROM person WHERE email!=%s AND fname=%s AND lname=%s AND '
            'email NOT IN (SELECT email FROM belong WHERE owner_email=%s AND fg_name=%s)')
    people = processQuery(query, [session['username'], firstName,lastName,session['username'],fg_name],True)
    #if empty, then there is no one under that name that you can add
    if(len(people) == 0):
        session['error'] = 'No one under ' + firstName + ' ' + lastName + ' is avaliable / can be added to ' + fg_name
        return redirect(url_for('home'))
    #if there is only one matching person, then just add them
    elif(len(people) == 1):
        query = 'INSERT INTO belong(email,owner_email, fg_name) VALUES (%s,%s,%s)'
        result = processQuery(query, [people[0]['email'], session['username'], fg_name], None, True)
        session['success'] = firstName + ' ' + lastName + ' has been added to ' + fg_name
        return redirect(url_for('home'))

    session['friendName'] = (firstName,lastName)
    #there are more than one matching tuples
    return render_template('addFriendConfirmation.html', people=people, fg_name=fg_name)

#adds the person once the user confirms who it should be.
@app.route('/addFriendConfirmation/email=<string:email>&fg_name=<string:fg_name>', methods=['GET','POST'])
def addFriendConfirmationProcess(email,fg_name):
    # checkSession() #for some reason, doesn't execute as expected
    if('username' not in session):
        error = 'User session invalid / expired. Please login.'
        session['error'] = error
        return redirect(url_for('index'))
    query = 'INSERT INTO belong(email,owner_email, fg_name) VALUES (%s,%s,%s)'
    result = processQuery(query,[email,session['username'], fg_name], None, True)

    session['success'] = session['friendName'][0] + ' ' + session['friendName'][1] + ' has been added to ' + fg_name
    session.pop('friendName')
    return redirect(url_for('home'))

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
