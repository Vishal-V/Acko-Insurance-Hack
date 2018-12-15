import os

from simple import app
if __name__ == '__main__':
        app.debug=True
        host=os.environ.get('IP','127.0.0.1')
        port=int(os.environ.get('PORT',8000))
        app.run(host=host,port=port)
