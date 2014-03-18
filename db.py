import sqlite3
from flask import g
from checklist import app

#THIS FILE CONTAINS FUNCTIONS THAT HELP WITH DATABASE INTERACTION

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

def query_db(query, args=(), one=False, script=False):
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