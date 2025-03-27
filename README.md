# ChatConnect

ChatConnect is a real-time chat application that connects users from the same city for spontaneous conversations. It leverages Flask, SocketIO, and SQLAlchemy to manage user sessions, chat rooms, and real-time messaging.

## Features
- **Location-based Matching**: Automatically connects users from the same city using IP-based geolocation.
- **Real-time Messaging**: Utilizes WebSockets via Flask-SocketIO for instant communication.
- **User Management**: Tracks user sessions and chat history with a SQLite database.
- **Scalable Architecture**: Designed to handle multiple concurrent users efficiently.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ChatConnect.git
   cd ChatConnect
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the root directory.
   - Add your secret key:
     ```env
     SECRET_KEY=your-secret-key
     ```

5. **Run the Application**:
   ```bash
   python app.py
   ```

6. **Access the Application**:
   - Open your browser and navigate to `http://localhost:5000`.

## Usage
- **Home Page**: Displays a welcome message and a "Start Chatting" button.
- **Chat Page**: Matches users from the same city. Once matched, users can exchange real-time messages in a chat room.

## Contribution
See the [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed guidelines on how to contribute to this project.

## License
This project is licensed under the MIT License.