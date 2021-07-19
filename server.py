from flask_app import socketio,app

if __name__=="__main__":
    socketio.run(app,debug=True)