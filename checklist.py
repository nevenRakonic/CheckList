import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, url_for
from flask import g, redirect, jsonify, session, flash
from flaskext.bcrypt import Bcrypt
#own modules
from decorators import login_required, permissions_required


app = Flask(__name__)
bcrypt = Bcrypt(app)
#app.config.from_envvar('CHECKLIST_SETTING')


#DB FUNCTIONS
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
    """Queries database, one is for one result only.
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def modify_db(query, args=()):
    """Used for queries that only modify the db and
    don't need to return anything
    """
    db = get_db()
    db.execute(query, args)
    db.commit()

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

#HELPER FUNCTIONS
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
    SELECT l.name, l.id, l.author, l.created
    FROM lists l, permissions p, users u
    WHERE  u.id = p.user_id
    AND l.id = p.list_id
    AND u.username = ?;
    """

    others_lists = query_db(others_query, [username])
    return render_template('home.html', own_lists=own_lists, others_lists=others_lists)

@app.route('/add_list', methods=['POST'])
@login_required
def add_list():
    """This view creates a new task list"""
    name = request.form['list_name']
    author = session['username']
    author_id = session['id']
    created = get_current_time()

    modify_db(
        'INSERT INTO lists (name, created, author_id, author) VALUES (?, ?, ?, ?);',
        [name, created, author_id, author]
        )


    session["permissions"] = get_permissions(session["id"], session["username"])
    flash(str(name) + " list added")
    return redirect(url_for('home'))

#TODOD refactor the way posts are shown
@app.route('/<int:list_id>/')
@login_required
@permissions_required
def show_list(list_id):
    """Shows all the posts in the list.
    Integer list_id is passed on from url
    to identify the list in the databse
    """

    author_query = """
    SELECT author, name
    FROM lists
    WHERE id = ?;
    """
    post_query = """
    SELECT l.author as list_author, l.name, l.created, p.body, p.status, p.id, p.post_time, p.author
    FROM lists l, posts p
    WHERE p.list_id = l.id
    AND l.id = ?
    ORDER BY p.post_time DESC;
    """
    posts = query_db(post_query, [list_id])

    if not posts:
        #this case only happens if there are no posts in the list yet
        #first index must be the author because it's the only query result
        list_data = query_db(author_query, [list_id], one=True)
        author = list_data[0]
        list_name = list_data[1]
    else:
        #extracts list author, no need for another query
        author = posts[0]["list_author"]
        list_name = posts[0]["name"]

    return render_template(
        'list_view.html',
        posts=posts,
        list_id=list_id,
        author=author,
        list_name=list_name)

@app.route('/<int:list_id>/add_permission', methods=['GET', 'POST'])
@login_required
@permissions_required
def add_permission(list_id):
    """Adds a permissions to see and manipulate a list
    that was not made by the user
    """
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
                modify_db(query, [username, list_id])
            except sqlite3.IntegrityError:
                flash("user already has permissions")
            else:
                flash("permission added")

    return redirect('/' + str(list_id) + '/')

@app.route('/<int:list_id>/add_post', methods=['POST'])
@login_required
@permissions_required
def add_post(list_id):
    """Add's a post to the list
    """
    body = request.form['body']
    body = "<br>".join(body.split("\n"))
    status = request.form['status']

    author = session["username"]
    post_time = get_current_time()

    modify_db(
        'INSERT INTO posts (list_id, body, status, post_time, author) VALUES (?, ?, ?, ?, ?);',
         [list_id, body, status, post_time, author]
         )
    #TODO lack of status

    flash("post added")
    return redirect("/{0}/".format(list_id))



#jeditable uses this edit function
@app.route('/<int:list_id>/edit', methods=['POST'])
@login_required
@permissions_required
def edit(list_id):
    """This function is used by jeditable
    jquery plugin to edit a post
    Jeditable turns a div into a textarea form
    """
    body = request.form['value']
    post_id = request.form['post_id']
    #turn newlines into html break lines
    body = "<br>".join(body.split("\n"))

    modify_db('UPDATE posts SET body=? WHERE ID=?', [body, post_id])

    return body

@app.route('/<int:list_id>/delete_list', methods=['GET'])
@login_required
@permissions_required
def delete_list(list_id):
    """Deletes the list and all the
    places it appears in the db
    """
    #table names can't be parameterized, use until cascade gets set up properly in the database
    modify_db('DELETE FROM lists WHERE id = ?;', [list_id])
    modify_db('DELETE FROM posts WHERE list_id = ?;', [list_id])
    modify_db('DELETE FROM permissions WHERE list_id = ?;', [list_id])

    flash("list deleted!")
    return redirect(url_for('home'))

@app.route('/<int:list_id>/delete_post', methods=['POST'])
@login_required
@permissions_required
def delete_post(list_id):
    """Deletes a post from the list via ajax"""
    data = request.get_json()
    data_id = data["id"]
    modify_db('DELETE FROM posts WHERE ID=?', [data_id])

    #needs to return something, so it only returns empty data
    return jsonify(result=None)

@app.route('/<int:list_id>/status', methods=['POST'])
@login_required
@permissions_required
def change_status(list_id):
    """Changes post status via ajax"""
    data = request.get_json()
    data_id = data["id"]
    status = data["status"]
    modify_db('UPDATE posts SET status=? WHERE ID=?', [status, data_id])

    return jsonify(result=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """This views shows the registration form.
    POST method adds the user to db if all the
    conditions are satisfied
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        duplicate_pass = request.form['duplicate_pass']

        #TODO refactor this
        if len(username) < 2:
            flash("username must have at least two characters")
            return render_template("register.html")
        if len(username) > 30:
            flash("username can't have more than 30 characters")
            return render_template("register.html")
        if find_username(username):
            flash("username already exists!")
            return render_template("register.html")
        if len(password) < 4:
            flash("password must contain at least 4 characters!")
            return render_template("register.html")
        if not password == duplicate_pass:
            flash("passwords didn't match")
            return render_template("register.html")


        password = bcrypt.generate_password_hash(request.form['password'])
        join_date = get_current_time()

        modify_db(
            'INSERT INTO users (username, password, join_date) VALUES (?, ?, ?);',
             [username, password, join_date]
             )

        flash("You can login with your account now")
        return redirect(url_for('home'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs in user, saves data to session"""
    if request.method == 'POST':
        logged_in = False

        username = request.form['username']
        password = request.form['password']
        user = query_db(
            'SELECT username, password, id FROM users WHERE username=?;', [username],
            one=True
            )

        if user:
            user = dict(user)   #dict is needed to convert the sqlite.row object to a dictionary
            logged_in = check_login(username, password, user)
        if logged_in:
            session["username"] = username
            session["id"] = user["id"]
            session["permissions"] = get_permissions(session["id"], username)

            return redirect(url_for('home'))
        flash("Login unsuccesful!")

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    """Logs the user out"""
    session.pop('username', None)
    session.pop('id', None)
    session.pop('permissions', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()
