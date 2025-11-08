import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime
import os
import requests
import threading
import socketio
import json
from queue import Queue
import time

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notes Application (Desktop)")
        self.root.geometry("600x550")
        self.root.configure(bg="#4CAF50")  # Green background to match web app
        
        # API Configuration - Updated for cloud deployment
        self.api_base_url = "https://laserclouding-hva2gweudafvadcw.canadacentral-01.azurewebsites.net"
        self.use_api = True
        self.socket_client = None
        self.update_queue = Queue()
        
        # Initialize database (as fallback)
        self.init_database()
        
        # Create GUI
        self.create_gui()
        
        # Initialize API connection
        self.init_api_connection()
        
        # Load existing notes
        self.load_notes()
        
        # Start update checker
        self.start_update_checker()
    
    def init_database(self):
        """Initialize SQLite database and create notes table if it doesn't exist"""
        self.db_path = "notes.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create notes table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def create_gui(self):
        """Create the main GUI interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#4CAF50", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Notes",
            font=("Arial", 24, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        title_label.pack(pady=(0, 20))
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg="#4CAF50")
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Text input area
        self.text_input = tk.Text(
            input_frame,
            height=4,
            width=50,
            font=("Arial", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add Note button
        add_button = tk.Button(
            input_frame,
            text="Add Note",
            command=self.add_note,
            bg="white",
            fg="#333",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        add_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Notes display area with scrollbar
        notes_frame = tk.Frame(main_frame, bg="#4CAF50")
        notes_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for notes
        self.canvas = tk.Canvas(notes_frame, bg="#4CAF50", highlightthickness=0)
        scrollbar = ttk.Scrollbar(notes_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#4CAF50")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg="#4CAF50")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="Connecting to server...",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.sync_label = tk.Label(
            status_frame,
            text="",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 9)
        )
        self.sync_label.pack(side=tk.RIGHT)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def init_api_connection(self):
        """Initialize connection to the web API server"""
        try:
            # Test if server is running
            response = requests.get(f"{self.api_base_url}/api/notes", timeout=3)
            if response.status_code == 200:
                self.use_api = True
                self.status_label.config(text="Connected to server", fg="lightgreen")
                self.sync_label.config(text="Real-time sync active")
                
                # Initialize socket connection
                self.init_socket_connection()
            else:
                self.use_api = False
                self.status_label.config(text="Server error - using local database", fg="yellow")
        except Exception as e:
            self.use_api = False
            self.status_label.config(text="Offline - using local database", fg="orange")
            print(f"API connection failed: {e}")
    
    def init_socket_connection(self):
        """Initialize WebSocket connection for real-time updates"""
        def connect_socket():
            try:
                self.socket_client = socketio.Client(logger=False, engineio_logger=False)
                
                @self.socket_client.event
                def connect():
                    print("Connected to WebSocket server")
                
                @self.socket_client.event
                def disconnect():
                    print("Disconnected from WebSocket server")
                
                @self.socket_client.event
                def note_added(data):
                    print(f"WebSocket: Note added - {data}")
                    # Add small delay to ensure database is updated
                    self.root.after(100, lambda: self.update_queue.put(('refresh', None)))
                
                @self.socket_client.event
                def note_deleted(data):
                    print(f"WebSocket: Note deleted - {data}")
                    # Add small delay to ensure database is updated
                    self.root.after(100, lambda: self.update_queue.put(('refresh', None)))
                
                # Connect to server
                self.socket_client.connect(self.api_base_url)
                
            except Exception as e:
                print(f"Socket connection failed: {e}")
                self.socket_client = None
        
        # Connect in background thread
        threading.Thread(target=connect_socket, daemon=True).start()
    
    def start_update_checker(self):
        """Start checking for real-time updates"""
        def check_updates():
            try:
                if not self.update_queue.empty():
                    action, data = self.update_queue.get_nowait()
                    if action == 'refresh':
                        # Refresh the display
                        self.load_notes()
            except:
                pass
            
            # Schedule next check
            self.root.after(100, check_updates)
        
        self.root.after(1000, check_updates)
    
    def add_note(self):
        """Add a new note via API or database"""
        content = self.text_input.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showwarning("Warning", "Please enter some text for the note!")
            return
        
        if self.use_api:
            try:
                # Use API
                response = requests.post(
                    f"{self.api_base_url}/api/notes",
                    json={"content": content},
                    timeout=5
                )
                
                if response.status_code == 200:
                    # Clear input
                    self.text_input.delete("1.0", tk.END)
                    # Immediately refresh to show the new note
                    self.load_notes()
                    # Also schedule another refresh to ensure we get the latest data
                    self.root.after(300, self.load_notes)
                    self.sync_label.config(text="Note synced ✓")
                    self.root.after(2000, lambda: self.sync_label.config(text="Real-time sync active"))
                else:
                    raise Exception(f"Server error: {response.status_code}")
                    
            except Exception as e:
                messagebox.showerror("Sync Error", f"Failed to sync with server: {e}\nSaving locally...")
                self.add_note_local(content)
        else:
            self.add_note_local(content)
    
    def add_note_local(self, content):
        """Add note to local database"""
        try:
            # Insert note into local database
            self.cursor.execute(
                "INSERT INTO notes (content) VALUES (?)",
                (content,)
            )
            self.conn.commit()
            
            # Clear input
            self.text_input.delete("1.0", tk.END)
            
            # Refresh notes display
            self.load_notes()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error saving note: {e}")
    
    def delete_note(self, note_id):
        """Delete a note via API or database"""
        result = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this note?"
        )
        
        if result:
            if self.use_api:
                try:
                    # Use API
                    response = requests.delete(
                        f"{self.api_base_url}/api/notes/{note_id}",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        # Notes will be updated via WebSocket
                        self.sync_label.config(text="Note deleted ✓")
                        self.root.after(2000, lambda: self.sync_label.config(text="Real-time sync active"))
                    else:
                        raise Exception(f"Server error: {response.status_code}")
                        
                except Exception as e:
                    messagebox.showerror("Sync Error", f"Failed to sync with server: {e}\nDeleting locally...")
                    self.delete_note_local(note_id)
            else:
                self.delete_note_local(note_id)
    
    def delete_note_local(self, note_id):
        """Delete note from local database"""
        try:
            self.cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            self.conn.commit()
            self.load_notes()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error deleting note: {e}")
    
    def load_notes(self):
        """Load and display all notes from API or database"""
        if self.use_api:
            self.refresh_notes_from_server()
        else:
            self.load_notes_local()
    
    def refresh_notes_from_server(self):
        """Refresh notes from API server"""
        try:
            response = requests.get(f"{self.api_base_url}/api/notes", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.display_notes(data['notes'])
                else:
                    raise Exception(data.get('error', 'Unknown error'))
            else:
                raise Exception(f"Server error: {response.status_code}")
        except Exception as e:
            print(f"Failed to load from server: {e}")
            # Fallback to local database
            self.use_api = False
            self.status_label.config(text="Server unavailable - using local data", fg="orange")
            self.load_notes_local()
    
    def load_notes_local(self):
        """Load and display all notes from local database"""
        try:
            # Fetch all notes from database
            self.cursor.execute("SELECT id, content, created_at FROM notes ORDER BY created_at DESC")
            notes = self.cursor.fetchall()
            
            # Convert to API format
            notes_list = []
            for note in notes:
                notes_list.append({
                    'id': note[0],
                    'content': note[1],
                    'created_at': note[2]
                })
            
            self.display_notes(notes_list)
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading notes: {e}")
    
    def display_notes(self, notes):
        """Display notes in the GUI"""
        # Clear existing notes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not notes:
            # Show message when no notes exist
            no_notes_label = tk.Label(
                self.scrollable_frame,
                text="No notes yet. Add your first note above!",
                bg="#4CAF50",
                fg="white",
                font=("Arial", 12, "italic")
            )
            no_notes_label.pack(pady=50)
            return
        
        # Display each note
        for note in notes:
            if isinstance(note, dict):
                self.create_note_widget(note['id'], note['content'], note['created_at'])
            else:
                # Handle tuple format (from local database)
                self.create_note_widget(note[0], note[1], note[2])
    
    def create_note_widget(self, note_id, content, created_at):
        """Create a widget for displaying a single note"""
        # Note container
        note_frame = tk.Frame(
            self.scrollable_frame,
            bg="white",
            relief=tk.RAISED,
            borderwidth=1
        )
        note_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Content frame (left side)
        content_frame = tk.Frame(note_frame, bg="white")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Note content
        content_label = tk.Label(
            content_frame,
            text=content,
            bg="white",
            fg="#333",
            font=("Arial", 11),
            justify=tk.LEFT,
            wraplength=450,
            anchor="w"
        )
        content_label.pack(anchor="w", fill=tk.X)
        
        # Timestamp
        timestamp_label = tk.Label(
            content_frame,
            text=f"Created: {created_at}",
            bg="white",
            fg="#666",
            font=("Arial", 9),
            anchor="w"
        )
        timestamp_label.pack(anchor="w", pady=(5, 0))
        
        # Delete button (right side)
        delete_button = tk.Button(
            note_frame,
            text="✗",
            command=lambda: self.delete_note(note_id),
            bg="#FF4444",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            width=3,
            height=1,
            cursor="hand2"
        )
        delete_button.pack(side=tk.RIGHT, padx=10, pady=10)
    
    def __del__(self):
        """Close database connection when app is destroyed"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = NotesApp(root)
    
    # Handle window closing
    def on_closing():
        if hasattr(app, 'conn'):
            app.conn.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()