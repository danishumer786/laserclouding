from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
import json
import threading
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

class NotesDatabase:
    def __init__(self, db_path="notes.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a new database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with notes table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_all_notes(self):
        """Get all notes from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, created_at FROM notes ORDER BY created_at DESC")
            return cursor.fetchall()
    
    def add_note(self, content):
        """Add a new note to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (content) VALUES (?)",
                (content,)
            )
            conn.commit()
            # Get the ID of the inserted note
            cursor.execute("SELECT id, content, created_at FROM notes WHERE id = ?", (cursor.lastrowid,))
            return cursor.fetchone()
    
    def delete_note(self, note_id):
        """Delete a note from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0

# Initialize database
db = NotesDatabase()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """API endpoint to get all notes"""
    try:
        notes = db.get_all_notes()
        notes_list = []
        for note in notes:
            notes_list.append({
                'id': note[0],
                'content': note[1],
                'created_at': note[2]
            })
        return jsonify({'success': True, 'notes': notes_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes', methods=['POST'])
def add_note():
    """API endpoint to add a new note"""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Note content cannot be empty'}), 400
        
        note = db.add_note(content)
        note_data = {
            'id': note[0],
            'content': note[1],
            'created_at': note[2]
        }
        
        # Broadcast the new note to all connected clients
        socketio.emit('note_added', note_data)
        
        return jsonify({'success': True, 'note': note_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """API endpoint to delete a note"""
    try:
        success = db.delete_note(note_id)
        if success:
            # Broadcast the deletion to all connected clients
            socketio.emit('note_deleted', {'id': note_id})
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_notes')
def handle_request_notes():
    """Handle request for all notes"""
    try:
        notes = db.get_all_notes()
        notes_list = []
        for note in notes:
            notes_list.append({
                'id': note[0],
                'content': note[1],
                'created_at': note[2]
            })
        emit('notes_update', {'notes': notes_list})
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
        os.makedirs('static/css')
        os.makedirs('static/js')
    
    # Get port from environment variable (for cloud deployment)
    port = int(os.environ.get('PORT', 5000))
    
    print("Starting Notes Web Application...")
    print(f"Access the web app at: http://localhost:{port}")
    print(f"API endpoints available at: http://localhost:{port}/api/notes")
    
    # Use different settings for production vs development
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port)