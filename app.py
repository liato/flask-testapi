import string
import random
import pprint
import time
from threading import Thread
from functools import wraps

from werkzeug.exceptions import HTTPException
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import abort
from flask import request
from flask import g

app = Flask(__name__)
app.config.from_object(__name__)

class InvalidRequest(HTTPException):
    code = 400
    message = "INVALID_REQUEST"
    def __init__(self, message):
        self.message = message

def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def route(url, *args, **kwargs):
    def deco(f):
        @app.route(url, *args, **kwargs)
        @wraps(f)
        def decorated(*args, **kwargs):
            response = f(*args, **kwargs)
            if isinstance(response, dict):
                response["success"] = True
                response = jsonify(response)
                response.headers['X-Hello'] = "Hello world!"
            return response
        return decorated

    return deco

def auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        abort(401)
    return decorated


@app.errorhandler(400)
@app.errorhandler(401)
def handle_error(error):
    response = {"success": False}
    if isinstance(error, InvalidRequest):
        response["code"] = error.message
    elif error.code == 401:
        response["code"] = "UNAUTHORIZED"
    else:
        response["code"] = "INVALID_REQUEST"
    return jsonify(response), error.code

@app.before_request
def before_request():
    g.responsestart = time.time()

@app.after_request
def after_request(response):
    response.headers['X-ExecutionTime'] = "%fms" % ((time.time()-g.responsestart)*1000)
    return response

@route('/')
def json_response():
    return {"hej": "blah"}

@route('/str')
def string_response():
    return "yo"

@route('/auth')
@auth
def auth_required_response():
    return "logged in"


@route('/validate', methods=["GET", "POST"])
def invalid_request_response():
    if request.method == "GET":
        return '<form method="POST">Enter "42": <input name="x" type="text" /><input type="submit" /></form>'
    elif request.method == "POST":
        print request.form
        if request.form.get("x", None) == "42":
            return "Yeah!"
        else:
            raise InvalidRequest("INVALID_ANSWER")



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5002)
