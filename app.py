import os
import time
from functools import wraps
from threading import Thread

from flask import Flask
from flask import abort
from flask import g
from flask import jsonify
from flask import request
from werkzeug.exceptions import HTTPException

from httpcodes import http_codes


class Flashk(Flask):
    def make_response(self, rv):
        if isinstance(rv, dict):
            rv["success"] = True
            rv = jsonify(rv)
            rv.headers['X-Hello'] = "Hello world!"
        return Flask.make_response(self, rv)

    def handle_http_exception(self, e):
        handlers = self.error_handler_spec.get(request.blueprint)
        # Proxy exceptions don't have error codes.  We want to always return
        # those unchanged as errors
        if e.code is None:
            return e
        if handlers and e.code in handlers:
            handler = handlers[e.code]
        else:
            handler = self.error_handler_spec[None].get(e.code)
        if handler is None:
            response = {"success": False}
            if isinstance(e, BadRequest):
                response["error"] = e.error
                if e.message:
                    response["message"] = e.message
            else:
                response["error"] = http_codes.get(e.code, str(e.code))
            return jsonify(response), e.code
        return handler(e)


app = Flashk(__name__)
app.config.from_object(__name__)


class BadRequest(HTTPException):
    code = 400

    def __init__(self, error, message=None):
        self.error = error
        self.message = message


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        abort(401)
    return decorated


@app.before_request
def before_request():
    g.responsestart = time.time()


@app.after_request
def after_request(response):
    response.headers['X-ExecutionTime'] = "%fms" % ((time.time()-g.responsestart)*1000)
    return response


@app.route('/')
def json_response():
    return {"hej": "blah"}


@app.route('/str')
def string_response():
    return "yo"


@app.route('/notimpl')
def not_implemented_response():
    abort(501)


@app.route('/auth')
@auth
def auth_required_response():
    return "logged in"


@app.route('/validate', methods=["GET", "POST"])
def invalid_request_response():
    if request.method == "GET":
        return '<form method="POST">Enter "42": <input name="x" type="text" /><input type="submit" /></form>'
    elif request.method == "POST":
        print request.form
        if request.form.get("x", None) == "42":
            return "Yeah!"
        else:
            raise BadRequest("INVALID_ANSWER", "you suck")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
