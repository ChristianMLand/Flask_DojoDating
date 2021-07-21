from datetime import datetime
from flask_socketio import join_room, emit
from flask import render_template,session,redirect
from flask_app import socketio,app,MESSAGE_COUNT
from flask_app.models.user_model import User
from flask_app.models.match_model import Match
from flask_app.models.direct_message_model import DirectMessage
from flask_app.config.orm2 import login_required

#----------------Display-----------------#
@app.route('/chat/<int:match_id>')
@login_required
def chat(match_id):
    logged_user = User.retrieve(id=session['id']).first()
    match = Match.retrieve(id=match_id).first()
    if not match or match and match not in logged_user.matches:#make sure the user has access to this chat
        return redirect('/matches')
    if match.matched.first() == logged_user:#depending on who was the last to like, logged_user could be matched or matcher
        other_user = match.matcher.first()
    else:
        other_user = match.matched.first()
    context = {
        'logged_user' : logged_user,
        'match' : match,
        'matched' : other_user
    }
    return render_template('chat.html', **context)
#----------------Listeners------------------#
@socketio.on('join_room')
def handle_join_room(data):
    join_room(f"{data['match_id']}")#join room based on match_id which is guaranteed unique
    emit('join_room',data,broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    msg_id = DirectMessage.create(
        match_id = data['match_id'],
        sender_id = data['sender_id'],
        content = data['content']
    )
    msg = DirectMessage.retrieve(id=msg_id).first()#retrieve newly created message to get timestamps
    msg_data = {
        "id" : msg.id,
        "sender_username" : data['sender_username'],
        "sender_id" : data['sender_id'],
        "content" : data['content'],
        "created_at" : datetime.strftime(msg.created_at,'%x %X'),
        "updated_at" : datetime.strftime(msg.updated_at,'%x %X')
    }
    emit('send_message',msg_data, room=f"{data['match_id']}")

@socketio.on('update_message')
def handle_update_message(data):
    DirectMessage.update(
        id=data['id'],
        content=data['content'],
        is_deleted=data['is_deleted']
    )
    msg = DirectMessage.retrieve(id=data['id']).first()#retrieve updated message to get timestamps
    msg_data = {
        "id" : msg.id,
        "sender_username" : data['sender_username'],
        "sender_id" : msg._sender_id,
        "content" : msg.content,
        "is_deleted" : msg.is_deleted,
        "created_at" : datetime.strftime(msg.created_at,'%x %X'),
        "updated_at" : datetime.strftime(msg.updated_at,'%x %X')
    }
    emit('update_message', msg_data, room=f"{data['match_id']}")

@socketio.on('load_messages')
def handle_load_messages(data):
    messages = (#retrieve next batch of messages from the db
        DirectMessage
        .retrieve(match_id=data['match_id'])
        .order_by(desc=True)
        .limit(MESSAGE_COUNT)
        .skip((data['page'])*MESSAGE_COUNT)
    )
    json_msgs = []
    for msg in messages:#convert messages to json data
        json_msgs.append(
            {
                "id" : msg.id,
                "is_deleted" : msg.is_deleted,
                "sender_id" : msg._sender_id,
                "match_id" : msg._match_id,
                "content" : msg.content,
                "created_at" : str(msg.created_at),
                "updated_at" : str(msg.updated_at),
                "sender_username" : msg.sender.first().username
            } 
        )
    emit('load_messages',{"messages" : json_msgs},json=True)
#-------------------------------------------#