from flask import render_template,redirect,request,session
from flask_app import app
from flask_app.models.user_model import User
from flask_app.models.match_model import Match
from flask_app.config.orm2 import login_required
import os
#----------------------Display----------------------------#
@app.get('/discover')
@login_required
def discover():
    logged_user = User.retrieve(id=session['id']).first()
    rand_user = (
        User.retrieve()
        .exclude(
            logged_user.seen_users,
            logged_user
        )
        .order_by(rand=True)
        .first()
    )
    context = {
        'logged_user' :logged_user,
        'rand_user' : rand_user
    }
    return render_template('discover.html', **context)

@app.get('/matches')
@login_required
def matches():
    return render_template('matches.html', logged_user=User.retrieve(id=session['id']).first())

@app.get('/profile')
@app.get('/profile/<int:id>')
@login_required
def view_profile(id=None):
    if not id:
        id = session['id']
    context = {
        "logged_user" : User.retrieve(id=session['id']).first(),
        "profile_user" : User.retrieve(id=id).first()
    }
    return render_template('view_profile.html', **context)

@app.get('/profile/edit')
@login_required
def edit_profile():
    return render_template('edit_profile.html', logged_user=User.retrieve(id=session['id']).first())
#----------------------Action-----------------------------#
@app.get('/like-user/<int:id>')
@login_required
def like_user(id):
    liker = User.retrieve(id=session['id']).first()
    liked = User.retrieve(id=id).first()
    liker.likes.add(liked)
    if liker in liked.likes:
        Match.create(
            matcher_id=session['id'],
            matched_id=id
        )
        return redirect('/matches')
    return redirect('/discover')

@app.get('/pass-user/<int:id>')
@login_required
def pass_user(id):
    passer = User.retrieve(id=session['id']).first()
    passer.passes.add(User.retrieve(id=id).first())
    return redirect('/discover')

@app.get('/unlike-user/<int:id>')
@login_required
def unlike_user(id):
    unliker = User.retrieve(id=session['id']).first()
    unliked = User.retrieve(id=id).first()
    Match.delete(matcher_id=session['id'],matched_id=id)
    Match.delete(matched_id=session['id'],matcher_id=id)
    unliker.likes.remove(unliked)
    return redirect('/discover')

@app.get('/reset-passes')
@login_required
def reset_passes():
    logged_user = User.retrieve(id=session['id']).first()
    logged_user.passes.remove(*logged_user.passes)
    return redirect('/discover')

@app.post('/profile/update')
@login_required
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