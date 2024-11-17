from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app)

active_rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-room')
def create_room():
    room_id = secrets.token_urlsafe(8)
    return redirect(url_for('room', room_id=room_id))

@app.route('/room/<room_id>')
def room(room_id):
    name = request.args.get('name', '')
    if not name:
        return redirect(url_for('index', room_id=room_id))
    return render_template('room.html', room_id=room_id, user_name=name)

@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    username = data.get('username', 'Anonymous')
    
    if room_id not in active_rooms:
        active_rooms[room_id] = {'users': set()}
    
    active_rooms[room_id]['users'].add(username)
    join_room(room_id)
    
    emit('user_joined', {
        'username': username,
        'user_count': len(active_rooms[room_id]['users'])
    }, room=room_id)

@socketio.on('leave')
def on_leave(data):
    room_id = data['room_id']
    username = data.get('username', 'Anonymous')
    
    if room_id in active_rooms:
        active_rooms[room_id]['users'].discard(username)
        if not active_rooms[room_id]['users']:
            del active_rooms[room_id]
    
    leave_room(room_id)
    emit('user_left', {
        'username': username,
        'user_count': len(active_rooms.get(room_id, {'users': set()})['users'])
    }, room=room_id)

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data['offer'], room=data['room_id'], skip_sid=request.sid)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data['answer'], room=data['room_id'], skip_sid=request.sid)

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    emit('ice-candidate', data['candidate'], room=data['room_id'], skip_sid=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)