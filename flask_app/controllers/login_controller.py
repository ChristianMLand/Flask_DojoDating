from flask import redirect, request, render_template, session
from flask_app.models.user_model import User
from flask_app import app,bcrypt

#----------------Display-----------------#
@app.get('/')
def index():
    if 'id' in session:
        return redirect('/discover')
    return render_template('index.html')
#----------------Action------------------#
@app.post('/users/register')
def register_user():
    if User.validate(**request.form):
        data = {
            **request.form,
            "password":bcrypt.generate_password_hash(request.form['password'])
        }
        session['id'] = User.create(**data)
        return redirect('/discover')
    return redirect('/')

@app.post('/users/login')
def login_user():
    if User.validate(**request.form):
        session['id'] = User.retrieve(email=request.form['login_email']).first().id
        return redirect('/discover')
    return redirect('/')

@app.get('/users/logout')
def logout_user():
    session.clear()
    return redirect('/')
#-----------------------------------------#