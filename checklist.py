import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, url_for
from flask import g, redirect, jsonify, session, flash
from flaskext.bcrypt import Bcrypt
#own modules
from decorators import login_required, permissions_required

#TODO define height in template for containers, fix buttons, end lists, add sorting/filtering via jquery
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.update(
    DEBUG=True,
    SECRET_KEY='oIOXe0CQufWKBR1B',
    DATABASE='db/test_db.db'
                )

#DATABSE HELPER METHODS
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Gets the database object"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
    return db

def query_db(query, args=(), one=False):
    """Queries database"""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def find_username(username):
    """Checks if username exists and returns username"""
    query = """
        SELECT username
        FROM users
        WHERE username=?;
        """
    return query_db(query, [username], one=True)

def get_permissions(user_id, username):
    """Returns IDs of posts that the user has permissions for"""
    other_query = """
    SELECT list_id
    FROM permissions
    WHERE user_id = ?;
    """

    self_query = """
    SELECT id
    FROM lists
    WHERE author = ?;
    """

    #list comprehension pulls out ids from sqlite.row object
    self_results = query_db(self_query, [username])
    self_results = [l[0] for l in self_results]
    other_results = query_db(other_query, [user_id])
    results = [l[0] for l in other_results]
    results.extend(self_results)

    return results

#closes db connection
@app.teardown_appcontext
def close_connection(exception):
    """Closes the connection to database"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#HELPER METHODS
def get_current_time():
    """Gets time, formatted to YYYY-MM-DD HH:MM:SS"""
    return str(datetime.now())[:-7]  #removes miliseconds from time

def check_login(username, password, user):
    """Checks login for username/pass
    from the form and compares it to
    the ones from the database (user dict)
    """
    return username == user["username"] and bcrypt.check_password_hash(user["password"], password)

#CONTROLLERS
@app.route('/')
@login_required
def home():
    """Home page view"""
    username = session["username"]
    #permissions are refreshed in case somebody else added a list we can see
    session["permissions"] = get_permissions(session["id"], username)

    own_query = """
    SELECT *
    FROM lists
    WHERE author = ?
    ORDER BY name DESC;
    """
    own_lists = query_db(own_query, [username])

    others_query = """
    SELECT l.name, l.id, l.author
    FROM lists l, permissions p, users u
    WHERE  u.id = p.user_id
    AND l.id = p.list_id
    AND u.username = ?;
    """

    others_lists = query_db(others_query, [username])
    return render_template('home.html', own_lists=own_lists, others_lists=others_lists)

@app.route('/add_list', methods=['GET', 'POST'])
@login_required
def add_list():
    """This view creates a new task list"""
    if request.method == 'POST':
        name = request.form['list_name']
        author = session['username']
        author_id = session['id']

        db = get_db()
        db.execute(
            'INSERT INTO lists (name, author_id, author) VALUES (?, ?, ?);',
             [name, author_id, author]
             )
        db.commit()
        session["permissions"] = get_permissions(session["id"], session["username"])
        flash(str(name) + " list added")
        return redirect(url_for('home'))
    #TODO Change template routing and check if list with same name exists
    return render_template('add_list.html')


@app.route('/<int:list_id>/')
@login_required
@permissions_required
def show_list(list_id):
    """Shows all the posts in the list.
    Integer list_id is passed on from url
    identify the list in the databse
    """

    author_query = """
    SELECT author
    FROM lists
    WHERE id = ?;
    """
    post_query = """
    SELECT l.author as list_author, p.body, p.status, p.id, p.post_time, p.author
    FROM lists l, posts p
    WHERE p.list_id = l.id
    AND l.id = ?
    ORDER BY p.post_time DESC;
    """
    posts = query_db(post_query, [list_id])

    if not posts:
        #first index must be the author because it's the only query result
        author = query_db(author_query, [list_id], one=True)[0]
    else:
        #extracts list author, no need for another query
        author = posts[0]["list_author"]
        #TODO add collapse to navbar
    print len(posts)
    return render_template('list_view.html', posts=posts, list_id=list_id, author=author)

@app.route('/<int:list_id>/add_permission', methods=['GET', 'POST'])
@login_required
@permissions_required
def add_permission(list_id):
    if request.method == 'POST':
        username = request.form['username']
        db_username = find_username(username)

        if not db_username:
            flash("user doesn't exist")
        elif session["username"] == username:
            flash("you already have permissions silly")
        else:
            query = """
            INSERT INTO permissions (user_id, list_id)
            SELECT u.id, l.id
            FROM users u, lists l
            WHERE u.username = ?
            AND l.id = ?;
            """

            #IntegrityError appears because user/list combo must be unique
            try:
                db = get_db()
                db.execute(query, [username, list_id])
                db.commit()
            except sqlite3.IntegrityError:
                flash("user already has permissions")
            else:
                flash("permission added")

    return redirect('/' + str(list_id) + '/')

@app.route('/<int:list_id>/add_post', methods=['GET', 'POST'])
@login_required
@permissions_required
def add_post(list_id):
    if request.method == 'POST':

        body = request.form['body']
        body = "<br>".join(body.split("\n"))
        status = request.form['status']
        author = session["username"]
        post_time = get_current_time()

        db = get_db()
        db.execute(
            'INSERT INTO posts (list_id, body, status, post_time, author) VALUES (?, ?, ?, ?, ?);',
             [list_id, body, status, post_time, author]
             )
        db.commit()

        flash("post added")
        return redirect("/{0}/".format(list_id))

    return render_template('add_post.html', list_id=list_id)

#jeditable uses this edit function
@app.route('/<int:list_id>/edit', methods=['POST'])
@login_required
@permissions_required
def edit(list_id):
    body = request.form['value']
    post_id = request.form['post_id']
    body = "<br>".join(body.split("\n"))


    db = get_db()
    db.execute('UPDATE posts SET body=? WHERE ID=?', [body, post_id])
    db.commit()

    return body

#ajax uses this delete function
@app.route('/<int:list_id>/delete', methods=['POST'])
@login_required
@permissions_required
def delete(list_id):
    if list_id in session["permissions"]:
        data = request.get_json()
        data_id = data["id"]

        db = get_db()
        db.execute('DELETE FROM posts WHERE ID=?', [data_id])
        db.commit()

        return jsonify(result=None) #needs to return something, so it only returns empty data

#ajax uses this function to change status
@app.route('/<int:list_id>/status', methods=['POST'])
@login_required
@permissions_required
def change_status(list_id):
    if list_id in session["permissions"]:
        data = request.get_json()

        data_id = data["id"]
        status = data["status"]

        db = get_db()
        db.execute('UPDATE posts SET status=? WHERE ID=?', [status, data_id])
        db.commit()

        return jsonify(result=None)
    return jsonify(result=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    #TODO Limit registration to 20 characters
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        duplicate_pass = request.form['duplicate_pass']

        if find_username(username):
            flash("username already exists!")
            return render_template("register.html")
        if not password == duplicate_pass:
            flash("passwords didn't match")
            return render_template("register.html")

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
            'SELECT username, password, id FROM users WHERE username=?;', [username],
            one=True
            )

        if user:
            user = dict(user)   #dict is needed to convert the sqlite.frow object to a dictionary
            logged_in = check_login(username, password, user)
        if logged_in:
            session["username"] = username
            session["id"] = user["id"]
            session["permissions"] = get_permissions(session["id"], username)

            return redirect(url_for('home'))
        #TODO add unsuccesfull login

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('id', None)
    session.pop('permissions', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()
