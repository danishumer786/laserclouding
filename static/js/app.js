class NotesWebApp {
    constructor() {
        this.socket = null;
        this.notes = [];
        this.isConnected = false;
        this.pollingInterval = null;
        
        console.log('🚀 Initializing Notes Web App...');
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadNotes(); // Load notes first
        this.connectToServer(); // Then try WebSocket connection
    }
    
    setupEventListeners() {
        // Add note button
        const addBtn = document.getElementById('addNoteBtn');
        const noteInput = document.getElementById('noteInput');
        
        addBtn.addEventListener('click', () => this.addNote());
        
        // Enter key in textarea (Ctrl+Enter to add note)
        noteInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.addNote();
            }
        });
    }
    
    connectToServer() {
        try {
            console.log('Attempting to connect to WebSocket...');
            
            // Configure Socket.IO with fallback options
            this.socket = io({
                timeout: 10000,
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 3,
                reconnectionDelay: 2000
            });
            
            this.socket.on('connect', () => {
                console.log('✅ WebSocket connected - real-time sync active!');
                this.isConnected = true;
                this.updateConnectionStatus(true, 'websocket');
                this.socket.emit('request_notes');
            });
            
            this.socket.on('disconnect', () => {
                console.log('📡 WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false, 'websocket');
            });
            
            this.socket.on('connect_error', (error) => {
                console.log('⚠️ WebSocket connection failed, using HTTP API mode');
                console.log('This is normal for Azure App Service without WebSocket enabled');
                this.isConnected = false;
                this.updateConnectionStatus(true, 'http'); // Still connected via HTTP
                
                // Set up polling for updates since WebSocket failed
                this.startHttpPolling();
            });
            
            this.socket.on('note_added', (noteData) => {
                console.log('🔄 Real-time update: Note added');
                this.addNoteToDisplay(noteData, false);
                this.showNotification('New note added!', 'success');
            });
            
            this.socket.on('note_deleted', (data) => {
                console.log('🗑️ Real-time update: Note deleted');
                this.removeNoteFromDisplay(data.id);
                this.showNotification('Note deleted!', 'success');
            });
            
            this.socket.on('notes_update', (data) => {
                console.log('📝 Notes update received:', data.notes.length, 'notes');
                this.updateNotesDisplay(data.notes);
            });
            
        } catch (error) {
            console.error('❌ WebSocket setup failed:', error);
            console.log('📡 Falling back to HTTP API mode');
            this.updateConnectionStatus(true, 'http'); // Fallback to HTTP
            this.startHttpPolling();
        }
        
        // Set initial status as HTTP mode until WebSocket connects
        setTimeout(() => {
            if (!this.isConnected) {
                console.log('⏰ WebSocket connection timeout, using HTTP mode');
                this.updateConnectionStatus(true, 'http');
                this.startHttpPolling();
            }
        }, 5000);
    }
    
    updateConnectionStatus(connected, mode = 'http') {
        const statusElement = document.getElementById('connectionStatus');
        const syncStatus = document.getElementById('syncStatus');
        
        if (connected) {
            if (mode === 'websocket') {
                statusElement.textContent = 'Online (Real-time)';
                statusElement.className = 'status online';
                syncStatus.textContent = 'WebSocket sync active ✓';
            } else {
                statusElement.textContent = 'Online (HTTP)';
                statusElement.className = 'status online';
                syncStatus.textContent = 'HTTP sync active (refresh for updates)';
            }
        } else {
            statusElement.textContent = 'Offline';
            statusElement.className = 'status offline';
            syncStatus.textContent = 'Offline mode - changes will sync when reconnected';
        }
    }
    
    startHttpPolling() {
        // Poll for updates every 30 seconds when WebSocket is not available
        console.log('🔄 Starting HTTP polling for updates...');
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        this.pollingInterval = setInterval(async () => {
            if (!this.isConnected) {
                try {
                    await this.loadNotes();
                } catch (error) {
                    console.log('Polling failed:', error);
                }
            }
        }, 30000);
    }
    
    async loadNotes() {
        try {
            const response = await fetch('/api/notes');
            const data = await response.json();
            
            if (data.success) {
                this.updateNotesDisplay(data.notes);
            } else {
                this.showNotification('Failed to load notes: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to load notes:', error);
            this.showNotification('Failed to load notes', 'error');
        }
    }
    
    async addNote() {
        const noteInput = document.getElementById('noteInput');
        const content = noteInput.value.trim();
        
        if (!content) {
            this.showNotification('Please enter some text for the note!', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content })
            });
            
            const data = await response.json();
            
            if (data.success) {
                noteInput.value = '';
                // Note will be added to display via socket event
                this.showNotification('Note added successfully!', 'success');
            } else {
                this.showNotification('Failed to add note: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to add note:', error);
            this.showNotification('Failed to add note', 'error');
        }
    }
    
    async deleteNote(noteId) {
        if (!confirm('Are you sure you want to delete this note?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/notes/${noteId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Note will be removed from display via socket event
                this.showNotification('Note deleted successfully!', 'success');
            } else {
                this.showNotification('Failed to delete note: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to delete note:', error);
            this.showNotification('Failed to delete note', 'error');
        }
    }
    
    updateNotesDisplay(notes) {
        this.notes = notes;
        const container = document.getElementById('notesContainer');
        const noNotesMessage = document.getElementById('noNotesMessage');
        
        // Clear existing notes (except no notes message)
        const existingNotes = container.querySelectorAll('.note-item');
        existingNotes.forEach(note => note.remove());
        
        if (notes.length === 0) {
            noNotesMessage.style.display = 'block';
        } else {
            noNotesMessage.style.display = 'none';
            
            // Add notes in order (server already sends newest first)
            notes.forEach(note => {
                this.addNoteToDisplayInOrder(note, true);
            });
        }
    }
    
    addNoteToDisplayInOrder(noteData, skipAnimation = false) {
        const container = document.getElementById('notesContainer');
        const noNotesMessage = document.getElementById('noNotesMessage');
        
        // Hide no notes message
        noNotesMessage.style.display = 'none';
        
        // Check if note already exists (to prevent duplicates)
        if (document.querySelector(`[data-note-id="${noteData.id}"]`)) {
            return;
        }
        
        const noteElement = document.createElement('div');
        noteElement.className = 'note-item';
        noteElement.setAttribute('data-note-id', noteData.id);
        
        if (skipAnimation) {
            noteElement.style.animation = 'none';
        }
        
        const createdDate = new Date(noteData.created_at).toLocaleString();
        
        noteElement.innerHTML = `
            <div class="note-content">
                <div class="note-text">${this.escapeHtml(noteData.content)}</div>
                <div class="note-timestamp">Created: ${createdDate}</div>
            </div>
            <button class="delete-btn" onclick="app.deleteNote(${noteData.id})">✗</button>
        `;
        
        // Simply append to container (notes come pre-sorted from server)
        container.appendChild(noteElement);
    }
    
    addNoteToDisplay(noteData, skipAnimation = false) {
        const container = document.getElementById('notesContainer');
        const noNotesMessage = document.getElementById('noNotesMessage');
        
        // Hide no notes message
        noNotesMessage.style.display = 'none';
        
        // Check if note already exists (to prevent duplicates)
        if (document.querySelector(`[data-note-id="${noteData.id}"]`)) {
            return;
        }
        
        const noteElement = document.createElement('div');
        noteElement.className = 'note-item';
        noteElement.setAttribute('data-note-id', noteData.id);
        
        if (skipAnimation) {
            noteElement.style.animation = 'none';
        }
        
        const createdDate = new Date(noteData.created_at).toLocaleString();
        
        noteElement.innerHTML = `
            <div class="note-content">
                <div class="note-text">${this.escapeHtml(noteData.content)}</div>
                <div class="note-timestamp">Created: ${createdDate}</div>
            </div>
            <button class="delete-btn" onclick="app.deleteNote(${noteData.id})">✗</button>
        `;
        
        // Add to the beginning of the container (newest notes first)
        const firstNote = container.querySelector('.note-item');
        if (firstNote) {
            container.insertBefore(noteElement, firstNote);
        } else {
            // If no notes exist, add after the no-notes message
            const noNotesMsg = container.querySelector('#noNotesMessage');
            if (noNotesMsg && noNotesMsg.nextSibling) {
                container.insertBefore(noteElement, noNotesMsg.nextSibling);
            } else {
                container.appendChild(noteElement);
            }
        }
    }
    
    removeNoteFromDisplay(noteId) {
        const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
        if (noteElement) {
            noteElement.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                noteElement.remove();
                
                // Show no notes message if no notes left
                const remainingNotes = document.querySelectorAll('.note-item');
                if (remainingNotes.length === 0) {
                    document.getElementById('noNotesMessage').style.display = 'block';
                }
            }, 300);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification(message, type = 'success') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Add slide out animation to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Initialize the app when page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM loaded, starting Notes Web App...');
    app = new NotesWebApp();
});

// Fallback initialization if DOMContentLoaded already fired
if (document.readyState === 'loading') {
    // Document still loading
} else {
    // Document already loaded
    if (typeof app === 'undefined') {
        console.log('📄 Document already loaded, starting Notes Web App...');
        app = new NotesWebApp();
    }
}