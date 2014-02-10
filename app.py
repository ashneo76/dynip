from flask import Flask, request
from flask_debugtoolbar import DebugToolbarExtension 
import optparse
from linode import api as l
import os


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'sicritkiy'
toolbar = DebugToolbarExtension(app)


@app.route('/update')
def default():
    ip = request.remote_addr
    b = 'Hello World! from ' + ip

    return b


def updateip(ip):
    api_key = os.environ['LINODE_API_KEY']


if __name__ == '__main__':
    app.run(host='0.0.0.0')
