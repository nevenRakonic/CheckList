import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, url_for
from flask import g, redirect, jsonify


app = Flask(__name__)
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'oIOXe0CQufWKBR1B',
    DATABASE = 'db/test_db.db'
    )

### DB METHODS
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

#ROUTES
@app.route('/')
def home():
    posts = query_db('SELECT * FROM posts ORDER BY post_time DESC;')
    return render_template('index.html', posts=posts)

@app.route('/add_post/', methods=['GET','POST'])
def add_post():
    if request.method == 'POST':
        db = get_db()

        body = request.form['body']
        comment = request.form['comment']
        status = request.form['status']
        post_time = str(datetime.now())
        post_time = post_time[:-7]  #removes miliseconds from time

        db.execute(
            'INSERT INTO posts (body, comment, status, post_time) VALUES (?, ?, ?, ?);',
             [body, comment, status, post_time]
             )
        db.commit()
        #TODO FLASH MESSAGE HERE
        return redirect(url_for('home'))

    return render_template('add_post.html')

@app.route('/<post_num>/showpost/')
def show_post(post_num):
    db = get_db()

    post = query_db('SELECT * FROM POSTS WHERE ID=%s' % post_num)
    return render_template('index.html', posts=post, edit=True)

#add editing ability
@app.route('/<post_num>/edit/', methods=['GET', 'POST'])
def edit_post(post_num):
    db = get_db()   
    
    if request.method == 'POST':
        text = request.form['text']

        db.execute('UPDATE posts SET body="{0}" WHERE ID={1}'.format(text, post_num))
        db.commit()
        #return redirect(url_for('home'))

    text = query_db('SELECT body FROM posts WHERE ID=%s' % post_num, one=True)    

    return render_template('edit.html', text=text, post_num=post_num)

#ajax uses this edit function
@app.route('/edit', methods=['POST'])
def edit():    
    db = get_db()

    data = request.get_json()
   
    body = data["body"]
    data_id = data["id"]
    

    db.execute('UPDATE posts SET body="{0}" WHERE ID={1}'.format(body, data_id))
    db.commit()         

    return jsonify(result=body)

#ajax uses this delete function
@app.route('/delete', methods=['POST'])
def delete():
    db = get_db()

    data = request.get_json()
    data_id = data["id"]

    db.execute('DELETE FROM posts WHERE ID=%s' % data_id)
    db.commit()

    return jsonify(result=None) #needs to return something, so it only returns empty data

@app.route('/status', methods=['POST'])
def change_status():
    db = get_db()

    data = request.get_json()
    data_id = data["id"]
    status = data["status"]
    print status

    db.execute('UPDATE posts SET status="{0}" WHERE ID={1}'.format(status, data_id))
    db.commit()

    return jsonify(result=None)


if __name__ == '__main__':
    app.run()