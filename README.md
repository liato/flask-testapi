## Installation
Create a virtualenv after cloning the project:

    $ cd flask-testapi
    $ virtualenv venv

Activate the virtualenv and install dependencies:

    $ source venv/bin/activate
    $ pip install -r requirements.txt

Run the project:

    $ gunicorn -w 4 -b 0.0.0.0:5000 -k gevent app:app
