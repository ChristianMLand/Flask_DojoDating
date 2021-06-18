from flask import render_template,redirect,request,session
from flask_app import app
from flask_app.models.user_model import User
import os
#----------------------Display----------------------------#
@app.get('/discover')
def discover():
    logged_user_q = User.retrieve(id=session['id'])
    logged_user = logged_user_q.first()
    rand_user = (User.retrieve()
                .exclude(
                    logged_user.seen_users,
                    logged_user_q
                )
                .order_by(rand=True)
                .first())
    context = {
        'logged_user' :logged_user,
        'rand_user' : rand_user
    }
    return render_template('discover.html', **context)

@app.get('/mutuals')
def mutuals():
    return render_template('mutuals.html', logged_user=User.retrieve(id=session['id']).first())

@app.get('/profile')
@app.get('/profile/<int:id>')
def view_profile(id=None):
    if not id:
        id = session['id']
    context = {
        "logged_user" : User.retrieve(id=session['id']).first(),
        "profile_user" : User.retrieve(id=id).first()
    }
    return render_template('view_profile.html', **context)

@app.get('/profile/edit')
def edit_profile():
    return render_template('edit_profile.html', logged_user=User.retrieve(id=session['id']).first())
#----------------------Action-----------------------------#
@app.get('/like-user/<int:id>')
def like_user(id):
    liker = User.retrieve(id=session['id']).first()
    liked = User.retrieve(id=id).first()
    liker.likes.add(liked)
    if liked in liker.mutuals:
        return redirect('/mutuals')
    return redirect('/discover')

@app.get('/pass-user/<int:id>')
def pass_user(id):
    passer = User.retrieve(id=session['id']).first()
    passer.passes.add(User.retrieve(id=id).first())
    return redirect('/discover')

@app.get('/unlike-user/<int:id>')
def unlike_user(id):
    unliker = User.retrieve(id=session['id']).first()
    unliker.likes.remove(User.retrieve(id=id).first())
    return redirect('/discover')

@app.get('/reset-passes')
def reset_passes():
    logged_user = User.retrieve(id=session['id']).first()
    logged_user.passes.remove(*logged_user.passes)
    return redirect('/discover')

@app.post('/profile/update')
def update_profile():
    if User.validate(**request.form):
        avatar = request.files.get('avatar')
        logged_user = User.retrieve(id=session['id']).first()
        if avatar:
            avatar.save(os.path.join(app.static_folder, f"img/{logged_user.id}.webp"))
        logged_user.update(
            gender=request.form['gender'],
            description=request.form['description'],
            avatar=f"{logged_user.id}.webp" if avatar else logged_user.avatar
        )
    return redirect('/profile')
#---------------------------------------------------------#