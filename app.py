from flask import Flask, render_template, request, session, jsonify, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
socketio = SocketIO(app)
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    """
    Represents a user in the chat system.
    """
    __tablename__ = 'user'
    id = db.Column(db.String(36), primary_key=True)
    location = db.Column(db.String(50), nullable=True)
    saved_chats = db.Column(db.Integer, default=0)

class Chat(db.Model):
    """
    Represents a chat session between two users.
    """
    __tablename__ = 'chat'
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    user2_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    room_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Drop all tables and recreate them
with app.app_context():
    db.drop_all()
    db.create_all()

def get_user_location():
    """
    Attempts to determine the user's location based on their IP address.
    If the location is not supported, defaults to Bangalore.
    """
    try:
        # Get IP address using ipapi.co
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        city = data.get('city', '').lower()
        
        # Check if city is in our supported cities list
        supported_cities = ['bangalore', 'mumbai', 'delhi', 'chennai', 'kolkata']
        if city in supported_cities:
            return city
        return 'bangalore'  # Default to Bangalore if city not supported
    except:
        return 'bangalore'  # Default to Bangalore if API fails

@app.route('/')
def home():
    """
    Handles the home page of the application.
    If the user is not logged in, creates a new user session.
    """
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        new_user = User(id=session['user_id'])
        # Automatically set user location
        new_user.location = get_user_location()
        db.session.add(new_user)
        db.session.commit()
    return render_template_string(HOME_TEMPLATE)

@app.route('/chat')
def chat():
    """
    Handles the chat page of the application.
    """
    return render_template_string(CHAT_TEMPLATE)

@app.route('/find_match')
def find_match():
    """
    Attempts to find a match for the current user based on their location.
    """
    user = User.query.get(session['user_id'])
    if user is None:
        return jsonify({'status': 'error', 'message': 'User not found'})
        
    if user.saved_chats >= 5:
        return jsonify({'status': 'error', 'message': 'Maximum chat limit reached'})
        
    potential_match = User.query.filter(
        User.location == user.location,
        User.id != session['user_id']
    ).first()
    
    if potential_match:
        room_id = str(uuid.uuid4())
        new_chat = Chat(
            user1_id=session['user_id'],
            user2_id=potential_match.id,
            room_id=room_id
        )
        user.saved_chats += 1
        db.session.add(new_chat)
        db.session.commit()
        return jsonify({'status': 'success', 'room_id': room_id})
    return jsonify({'status': 'waiting'})

# HTML Templates as strings
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to ChatConnect</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .welcome-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            padding: 2rem;
            margin-top: 2rem;
            text-align: center;
        }
        .btn-start {
            background: #4CAF50;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }
        .btn-start:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8 col-lg-6">
                <div class="welcome-card">
                    <h1 class="display-4 mb-4">ChatConnect</h1>
                    <p class="lead mb-4">Connect with people from your city in real-time conversations</p>
                    <a href="{{ url_for('chat') }}" class="btn btn-start btn-lg">Start Chatting</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Room - ChatConnect</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .chat-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-top: 2rem;
        }
        #messages {
            height: 400px;
            overflow-y: auto;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .message {
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 10px;
            max-width: 80%;
        }
        .message.sent {
            background: #2196F3;
            color: white;
            margin-left: auto;
        }
        .message.received {
            background: #E9ECEF;
        }
        .btn-action {
            border-radius: 20px;
            padding: 8px 20px;
            margin: 0 5px;
            transition: all 0.3s ease;
        }
        #waiting {
            text-align: center;
            padding: 2rem;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .spinner-border {
            width: 3rem;
            height: 3rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div id="waiting" class="mb-4">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h3>Looking for a chat partner...</h3>
                    <p class="text-muted">Please wait while we connect you with someone</p>
                </div>
                
                <div id="chatRoom" class="chat-container d-none">
                    <div id="messages"></div>
                    <form id="messageForm" class="mt-3">
                        <div class="input-group">
                            <input type="text" id="message" class="form-control" 
                                   placeholder="Type your message..." required
                                   aria-label="Type your message">
                            <button type="submit" class="btn btn-primary">Send</button>
                        </div>
                    </form>
                    <div class="d-flex justify-content-center mt-3">
                        <button onclick="reportUser()" class="btn btn-warning btn-action">
                            <i class="fas fa-flag"></i> Report
                        </button>
                        <button onclick="blockUser()" class="btn btn-danger btn-action">
                            <i class="fas fa-ban"></i> Block
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const socket = io();
        let currentRoom = null;

        async function findMatch() {
            const response = await fetch('/find_match');
            const data = await response.json();
            
            if (data.status === 'success') {
                currentRoom = data.room_id;
                document.getElementById('waiting').classList.add('d-none');
                document.getElementById('chatRoom').classList.remove('d-none');
                socket.emit('join', {room: currentRoom});
            } else if (data.status === 'waiting') {
                setTimeout(findMatch, 2000);
            } else if (data.status === 'error') {
                alert(data.message);
                window.location.href = '/';
            }
        }

        findMatch();

        document.getElementById('messageForm').onsubmit = (e) => {
            e.preventDefault();
            const messageInput = document.getElementById('message');
            const message = messageInput.value.trim();
            if (message) {
                socket.emit('message', {
                    room: currentRoom,
                    msg: message
                });
                messageInput.value = '';
            }
        };

        socket.on('message', (data) => {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${data.user === '${session["user_id"]}' ? 'sent' : 'received'}`;
            messageDiv.textContent = data.msg;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    socketio.run(app, debug=True)
