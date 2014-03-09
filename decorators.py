from functools import wraps
from flask import session, redirect, url_for

#DECORATOR METHODS
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs ):
        if "username" not in session:
            return redirect(url_for('login'))
        print kwargs
        return f(*args, **kwargs)
    return decorated_function




