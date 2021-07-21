const socket = io.connect('http://127.0.0.1:5000');
const messages = document.getElementById('messages');
const form = document.querySelector('form');
const load_messages = document.getElementById('loadMessages');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');
//-------------------------Listeners--------------------//
socket.on('connect', () => {
    socket.emit('join_room', {
        username : username,
        match_id: match_id,
        user_id: user_id
    });
    setupSendMessage();
    setupLoadMessages();
});

socket.on('join_room', data => {
    console.log(`${data.username} joined the chat`)
});

socket.on('send_message', data => {
    messages.prepend(createMessageComponent(data))
});

socket.on('update_message', data => {
    const myMsg = document.querySelector(`li[data-message_id='${data.id}']`)
    messages.replaceChild(createMessageComponent(data),myMsg)
});

socket.on('load_messages', data => {
    for(let msg of data.messages){
        messages.appendChild(createMessageComponent(msg));
    }
});
//-----------------------------Handlers-----------------------//
function handleSendMessage(){
    socket.emit('send_message', {
        sender_username: username,
        match_id: match_id,
        sender_id: user_id,
        content: msgInput.value.trim()
    });
    setupSendMessage();
}

function handleEditMessage(msg_id){
    socket.emit('update_message', {
        id : msg_id,
        sender_username : username,
        match_id: match_id,
        sender_id: user_id,
        content : msgInput.value.trim(),
        is_deleted : false
    });
    setupSendMessage();
}

function handleDeleteMessage(msg_id){
    socket.emit('update_message', {
        id : msg_id,
        sender_username : username,
        match_id: match_id,
        sender_id: user_id,
        content : 'This message has been deleted by the user',
        is_deleted : true
    });
}

function handleLoadMessages(page){
    socket.emit('load_messages', {
        match_id: match_id,
        page: page,
    });
}
//------------------------Setup---------------//
function setupSendMessage(){
    sendBtn.value = "Send";
    form.reset();
    msgInput.focus();
    form.onsubmit = e => {
        e.preventDefault();
        handleSendMessage();
    }
}

function setupLoadMessages(page=0){
    load_messages.onclick = e => {
        e.preventDefault();
        handleLoadMessages(page++);
    }
    load_messages.click()
}

function setupEditMessage(msg_id){
    const msgBody = document.querySelector(`li[data-message_id='${msg_id}'] .msgBody`);
    msgInput.value = msgBody.innerText;
    sendBtn.value = "Update";
    form.onsubmit = e => {
        e.preventDefault();
        handleEditMessage(msg_id);
    }
}
//---------------Utility----------------------//
function createMessageComponent(msg){
    const li = document.createElement('li');
    li.setAttribute('data-sender_id',msg.sender_id);
    li.setAttribute('data-message_id', msg.id);
    li.classList.add('d-flex','align-items-center','list-group-item','list-group-item-action');

    const div = document.createElement('div');
    div.classList.add('col-10','mr-auto');

    const msgHead = document.createElement('p');
    msgHead.classList.add('msgHead','bold');
    msgHead.innerText = `${msg.sender_username} [${msg.updated_at}]`;
    if(!msg.is_deleted && msg.created_at != msg.updated_at){
        msgHead.append(document.createTextNode(' (edited)'))
    }

    const msgBody = document.createElement('p');
    msgBody.classList.add('msgBody');
    msgBody.innerText = `${msg.content}`;
    if(msg.is_deleted == true){
        msgBody.classList.add('bold');
    }

    div.append(msgHead,msgBody);
    li.append(div);

    if(msg.sender_id == user_id && !msg.is_deleted){
        const editBtn = document.createElement('button');
        editBtn.onclick = e => setupEditMessage(msg.id);
        editBtn.classList.add('btn','btn-outline-secondary');
        editBtn.innerText = 'Edit';
        editBtn.style.display = 'none';

        const deleteBtn = document.createElement('button');
        deleteBtn.onclick = e => handleDeleteMessage(msg.id);
        deleteBtn.classList.add('btn','btn-outline-danger');
        deleteBtn.innerText = 'Delete';
        deleteBtn.style.display = 'none';

        li.append(editBtn,deleteBtn);
    }

    li.onmouseover = e => li.querySelectorAll('button').forEach(btn => btn.style.display = 'inline');
    li.onmouseout = e => li.querySelectorAll('button').forEach(btn => btn.style.display = 'none');

    return li;
}
//--------------------------------------------//
