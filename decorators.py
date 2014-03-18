from functools import wraps
from flask import session, redirect, url_for, flash
import constants

#DECORATOR FUNCTIONS
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs ):
        if "username" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def permissions_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs ):
        if kwargs.get("list_id"):
            list_id = kwargs["list_id"]
            if not list_id in session["permissions"]:
                flash(constants.EXIST_AUTHORIZE_W)
                return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function




