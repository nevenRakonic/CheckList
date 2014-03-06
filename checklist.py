import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, url_for
from flask import g, redirect, jsonify, session
from flaskext.bcrypt import Bcrypt


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'oIOXe0CQufWKBR1B',
    DATABASE = 'db/test_db.db'
    )

#DB METHODS
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    db = getattr(g,'_database', None)
    if db is None:
        db = g._database = connect_db()
    return db

def query_db(query, args=(), one=False):    
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#DECORATOR METHODS
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#HELPER METHODS
def get_current_time():
    return str(datetime.now())[:-7]  #removes miliseconds from time

def check_login(username, password, user):
    return username == user["username"] and bcrypt.check_password_hash(user["password"] ,password)  

#CONTROLLERS
@app.route('/')
@login_required
def home():    
    user_id = session["id"]
    posts = query_db('SELECT * FROM posts WHERE user_id="{0}" ORDER BY post_time DESC;'.format(user_id))    
    return render_template('index.html', posts=posts)
    

@app.route('/add_post', methods=['GET','POST'])
@login_required
def add_post():
    if request.method == 'POST':
        db = get_db()

        body = request.form['body']
        comment = request.form['comment']
        status = request.form['status']
        user_id = session["id"]
        post_time = get_current_time()

        db.execute(
            'INSERT INTO posts (user_id, body, comment, status, post_time) VALUES (?, ?, ?, ?, ?);',
             [user_id ,body, comment, status, post_time]
             )
        db.commit()
        #TODO FLASH MESSAGE HERE
        return redirect(url_for('home'))

    return render_template('add_post.html')

#ajax calls this to fill out new post fragments
@app.route('/<post_num>/show_post')
@login_required
def show_post(post_num):
    db = get_db()

    post = query_db('SELECT * FROM POSTS WHERE ID=%s' % post_num, one=True)

    return render_template('post_fragment.html', post=post)

#add editing ability
#LEGACY
@app.route('/<post_num>/edit/', methods=['GET', 'POST'])
@login_required
def edit_post(post_num):
       
    
    if request.method == 'POST':
        text = request.form['text']

        db = get_db()
        db.execute('UPDATE posts SET body="{0}" WHERE ID={1}'.format(text, post_num))
        db.commit()
        #return redirect(url_for('home'))

    text = query_db('SELECT body FROM posts WHERE ID=%s' % post_num, one=True)    

    return render_template('edit.html', text=text, post_num=post_num)

#jeditable uses this edit function
@app.route('/edit', methods=['POST'])
@login_required
def edit():  
    body = request.form['value']
    post_id = request.form['post_id']
    body = "<br />".join(body.split("\n"))
    
     
    db = get_db()
    db.execute('UPDATE posts SET body="{0}" WHERE ID={1}'.format(body, post_id))
    db.commit()        

    return body
    

#ajax uses this delete function
@app.route('/delete', methods=['POST'])
@login_required
def delete():
    data = request.get_json()    
    data_id = data["id"]

    db = get_db()
    db.execute('DELETE FROM posts WHERE ID=%s' % data_id)
    db.commit()

    return jsonify(result=None) #needs to return something, so it only returns empty data

#ajax uses this function to change status
@app.route('/status', methods=['POST'])
@login_required
def change_status():
    data = request.get_json()
    data_id = data["id"]
    status = data["status"]    

    db = get_db()
    db.execute('UPDATE posts SET status="{0}" WHERE ID={1}'.format(status, data_id))
    db.commit()

    return jsonify(result=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password'])         
        join_date = get_current_time()

        db = get_db()
        db.execute(
            'INSERT INTO users (username, password, join_date) VALUES (?, ?, ?);',
             [username, password, join_date]
             )
        db.commit()
        return redirect(url_for('home'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        logged_in = False

        username = request.form['username']
        password = request.form['password']
        user = query_db(
            'SELECT username, password, id FROM users WHERE username="{0}"'.format(username), 
            one=True
            )        

        if user:
            user = dict(user)   #dict is needed to convert the sqlite.frow object to a dictionary
            logged_in = check_login(username, password, user)
        if logged_in:
            session["username"] = username
            session["id"] = user["id"]
            return redirect(url_for('home'))

    return render_template("login.html")

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()