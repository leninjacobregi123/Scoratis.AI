import sqlite3
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self, db_path='scoratis.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#8A2BE2',
                user_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create journals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT, -- JSON array of tags
                folder_id INTEGER,
                user_id INTEGER DEFAULT 1,
                is_shared BOOLEAN DEFAULT FALSE,
                share_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create video_history table for tracking watched videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                channel TEXT,
                thumbnail_url TEXT,
                search_query TEXT,
                user_id INTEGER DEFAULT 1,
                watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create user_preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'en',
                auto_save BOOLEAN DEFAULT TRUE,
                notification_settings TEXT, -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create conversations table for chat history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                title TEXT,
                user_id INTEGER DEFAULT 1,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create chat_messages table for individual messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL, -- 'user' or 'ai'
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        ''')
        
        # Insert default user if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email) 
            VALUES (1, 'Lenin', 'lenin@scoratis.com')
        ''')
        
        # Insert default preferences if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO user_preferences (user_id) VALUES (1)
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a database query with error handling"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                result = cursor.fetchall()
                return [dict(row) for row in result]
            else:
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # Journal operations
    def create_journal(self, title, content, tags=None, folder_id=None, user_id=1):
        """Create a new journal entry"""
        tags_json = json.dumps(tags) if tags else None
        query = '''
            INSERT INTO journals (title, content, tags, folder_id, user_id, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        return self.execute_query(query, (title, content, tags_json, folder_id, user_id))
    
    def get_journals(self, user_id=1, folder_id=None, search_query=None):
        """Get all journals for a user with optional filtering"""
        query = '''
            SELECT j.*, f.name as folder_name 
            FROM journals j
            LEFT JOIN folders f ON j.folder_id = f.id
            WHERE j.user_id = ?
        '''
        params = [user_id]
        
        if folder_id:
            query += ' AND j.folder_id = ?'
            params.append(folder_id)
        
        if search_query:
            query += ' AND (j.title LIKE ? OR j.content LIKE ? OR j.tags LIKE ?)'
            search_param = f'%{search_query}%'
            params.extend([search_param, search_param, search_param])
        
        query += ' ORDER BY j.updated_at DESC'
        
        journals = self.execute_query(query, params, fetch=True)
        
        # Parse tags JSON
        for journal in journals:
            if journal['tags']:
                journal['tags'] = json.loads(journal['tags'])
            else:
                journal['tags'] = []
        
        return journals
    
    def update_journal(self, journal_id, title=None, content=None, tags=None, folder_id=None):
        """Update an existing journal"""
        updates = []
        params = []
        
        if title is not None:
            updates.append('title = ?')
            params.append(title)
        if content is not None:
            updates.append('content = ?')
            params.append(content)
        if tags is not None:
            updates.append('tags = ?')
            params.append(json.dumps(tags))
        if folder_id is not None:
            updates.append('folder_id = ?')
            params.append(folder_id)
        
        if not updates:
            return False
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(journal_id)
        
        query = f'UPDATE journals SET {", ".join(updates)} WHERE id = ?'
        self.execute_query(query, params)
        return True
    
    def delete_journal(self, journal_id, user_id=1):
        """Delete a journal entry"""
        query = 'DELETE FROM journals WHERE id = ? AND user_id = ?'
        self.execute_query(query, (journal_id, user_id))
        return True
    
    def share_journal(self, journal_id, user_id=1):
        """Toggle journal sharing status and generate share token"""
        import secrets
        share_token = secrets.token_urlsafe(16)
        query = '''
            UPDATE journals 
            SET is_shared = NOT is_shared, share_token = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        '''
        self.execute_query(query, (share_token, journal_id, user_id))
        return share_token
    
    # Folder operations
    def create_folder(self, name, description=None, color='#8A2BE2', user_id=1):
        """Create a new folder"""
        query = '''
            INSERT INTO folders (name, description, color, user_id, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        return self.execute_query(query, (name, description, color, user_id))
    
    def get_folders(self, user_id=1):
        """Get all folders for a user"""
        query = '''
            SELECT f.*, COUNT(j.id) as journal_count
            FROM folders f
            LEFT JOIN journals j ON f.id = j.folder_id
            WHERE f.user_id = ?
            GROUP BY f.id
            ORDER BY f.updated_at DESC
        '''
        return self.execute_query(query, (user_id,), fetch=True)
    
    def update_folder(self, folder_id, name=None, description=None, color=None):
        """Update an existing folder"""
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        if color is not None:
            updates.append('color = ?')
            params.append(color)
        
        if not updates:
            return False
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(folder_id)
        
        query = f'UPDATE folders SET {", ".join(updates)} WHERE id = ?'
        self.execute_query(query, params)
        return True
    
    def delete_folder(self, folder_id, user_id=1):
        """Delete a folder and move its journals to uncategorized"""
        # First, update journals to remove folder reference
        self.execute_query('UPDATE journals SET folder_id = NULL WHERE folder_id = ?', (folder_id,))
        # Then delete the folder
        query = 'DELETE FROM folders WHERE id = ? AND user_id = ?'
        self.execute_query(query, (folder_id, user_id))
        return True
    
    # Video history operations
    def add_video_to_history(self, video_id, title, channel, thumbnail_url, search_query, user_id=1):
        """Add a video to watch history"""
        query = '''
            INSERT OR REPLACE INTO video_history 
            (video_id, title, channel, thumbnail_url, search_query, user_id, watched_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        return self.execute_query(query, (video_id, title, channel, thumbnail_url, search_query, user_id))
    
    def get_video_history(self, user_id=1, limit=50):
        """Get video watch history"""
        query = '''
            SELECT * FROM video_history 
            WHERE user_id = ? 
            ORDER BY watched_at DESC 
            LIMIT ?
        '''
        return self.execute_query(query, (user_id, limit), fetch=True)
    
    # Conversation operations
    def create_conversation(self, session_id, user_id=1, title=None):
        """Create a new conversation record"""
        query = '''
            INSERT INTO conversations (session_id, title, user_id, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        return self.execute_query(query, (session_id, title, user_id))
    
    def get_or_create_conversation(self, session_id, user_id=1):
        """Get existing conversation or create new one"""
        # Try to get existing conversation
        query = 'SELECT id FROM conversations WHERE session_id = ? AND user_id = ?'
        result = self.execute_query(query, (session_id, user_id), fetch=True)
        
        if result:
            return result[0]['id']
        else:
            # Create new conversation
            return self.create_conversation(session_id, user_id)
    
    def add_chat_message(self, session_id, sender, message, user_id=1):
        """Add a message to the conversation"""
        # Get or create conversation
        conversation_id = self.get_or_create_conversation(session_id, user_id)
        
        # Add the message
        query = '''
            INSERT INTO chat_messages (conversation_id, session_id, sender, message)
            VALUES (?, ?, ?, ?)
        '''
        self.execute_query(query, (conversation_id, session_id, sender, message))
        
        # Update conversation timestamp and generate title if needed
        self.update_conversation_activity(conversation_id, message if sender == 'user' else None)
        
        return conversation_id
    
    def update_conversation_activity(self, conversation_id, user_message=None):
        """Update conversation timestamp and generate title if needed"""
        # Update timestamp
        self.execute_query('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (conversation_id,))
        
        # Generate title from first user message if no title exists
        if user_message:
            result = self.execute_query('SELECT title FROM conversations WHERE id = ?', (conversation_id,), fetch=True)
            if result and not result[0]['title']:
                # Create title from first few words of user message
                title = user_message[:50] + ('...' if len(user_message) > 50 else '')
                self.execute_query('UPDATE conversations SET title = ? WHERE id = ?', (title, conversation_id))
    
    def get_conversation_messages(self, session_id, user_id=1):
        """Get all messages for a conversation"""
        query = '''
            SELECT cm.sender, cm.message, cm.timestamp
            FROM chat_messages cm
            JOIN conversations c ON cm.conversation_id = c.id
            WHERE cm.session_id = ? AND c.user_id = ?
            ORDER BY cm.timestamp ASC
        '''
        return self.execute_query(query, (session_id, user_id), fetch=True)
    
    def get_conversation_history(self, user_id=1, limit=20, include_deleted=False):
        """Get list of recent conversations"""
        where_clause = "WHERE c.user_id = ?"
        params = [user_id]
        
        if not include_deleted:
            where_clause += " AND (c.is_deleted = FALSE OR c.is_deleted IS NULL)"
        else:
            where_clause += " AND c.is_deleted = TRUE"
        
        query = f'''
            SELECT c.id, c.session_id, c.title, c.created_at, c.updated_at, c.deleted_at,
                   COUNT(cm.id) as message_count,
                   MAX(cm.timestamp) as last_message_time
            FROM conversations c
            LEFT JOIN chat_messages cm ON c.id = cm.conversation_id
            {where_clause}
            GROUP BY c.id, c.session_id, c.title, c.created_at, c.updated_at, c.deleted_at
            ORDER BY c.updated_at DESC
            LIMIT ?
        '''
        params.append(limit)
        return self.execute_query(query, params, fetch=True)
    
    def clear_conversation(self, session_id, user_id=1):
        """Clear/delete a conversation and all its messages"""
        # Get conversation ID
        query = 'SELECT id FROM conversations WHERE session_id = ? AND user_id = ?'
        result = self.execute_query(query, (session_id, user_id), fetch=True)
        
        if result:
            conversation_id = result[0]['id']
            # Delete messages (CASCADE should handle this, but being explicit)
            self.execute_query('DELETE FROM chat_messages WHERE conversation_id = ?', (conversation_id,))
            # Delete conversation
            self.execute_query('DELETE FROM conversations WHERE id = ?', (conversation_id,))
            return True
        return False
    
    def delete_conversation(self, conversation_id, user_id=1, permanent=False):
        """Move conversation to trash or permanently delete it"""
        if permanent:
            # Permanently delete conversation and its messages
            self.execute_query('DELETE FROM chat_messages WHERE conversation_id = ?', (conversation_id,))
            query = 'DELETE FROM conversations WHERE id = ? AND user_id = ?'
        else:
            # Soft delete - move to trash
            query = '''
                UPDATE conversations 
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            '''
        
        self.execute_query(query, (conversation_id, user_id))
        return True
    
    def restore_conversation(self, conversation_id, user_id=1):
        """Restore conversation from trash"""
        query = '''
            UPDATE conversations 
            SET is_deleted = FALSE, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        '''
        self.execute_query(query, (conversation_id, user_id))
        return True
    
    def empty_trash(self, user_id=1):
        """Permanently delete all conversations in trash"""
        # Get all trashed conversation IDs
        trashed_conversations = self.execute_query(
            'SELECT id FROM conversations WHERE user_id = ? AND is_deleted = TRUE',
            (user_id,), fetch=True
        )
        
        # Delete all messages for trashed conversations
        for conv in trashed_conversations:
            self.execute_query('DELETE FROM chat_messages WHERE conversation_id = ?', (conv['id'],))
        
        # Delete all trashed conversations
        self.execute_query('DELETE FROM conversations WHERE user_id = ? AND is_deleted = TRUE', (user_id,))
        return True
    
    # Statistics
    def get_user_stats(self, user_id=1):
        """Get user statistics"""
        stats = {}
        
        # Journal count
        result = self.execute_query('SELECT COUNT(*) as count FROM journals WHERE user_id = ?', (user_id,), fetch=True)
        stats['total_journals'] = result[0]['count'] if result else 0
        
        # Folder count
        result = self.execute_query('SELECT COUNT(*) as count FROM folders WHERE user_id = ?', (user_id,), fetch=True)
        stats['total_folders'] = result[0]['count'] if result else 0
        
        # Videos watched
        result = self.execute_query('SELECT COUNT(*) as count FROM video_history WHERE user_id = ?', (user_id,), fetch=True)
        stats['videos_watched'] = result[0]['count'] if result else 0
        
        # Recent activity
        result = self.execute_query('''
            SELECT COUNT(*) as count FROM journals 
            WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
        ''', (user_id,), fetch=True)
        stats['journals_this_week'] = result[0]['count'] if result else 0
        
        # Conversation count
        result = self.execute_query('SELECT COUNT(*) as count FROM conversations WHERE user_id = ?', (user_id,), fetch=True)
        stats['total_conversations'] = result[0]['count'] if result else 0
        
        return stats