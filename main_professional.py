from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import secrets
import socket
from datetime import datetime, timedelta
from database import DatabaseManager

# Import APIs with lazy loading to avoid startup delays
import importlib

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize database
db = DatabaseManager()

# Global variables for API clients
_genai = None
_youtube_client = None

def get_genai():
    """Lazy load Google Generative AI"""
    global _genai
    if _genai is None:
        try:
            genai_module = importlib.import_module('google.generativeai')
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai_module.configure(api_key=api_key)
                _genai = genai_module
            else:
                print("Warning: GEMINI_API_KEY not found")
        except ImportError:
            print("Warning: google.generativeai not available")
    return _genai

def get_youtube_client():
    """Lazy load YouTube API client"""
    global _youtube_client
    if _youtube_client is None:
        try:
            from googleapiclient.discovery import build
            api_key = os.getenv("YOUTUBE_API_KEY")
            if api_key:
                _youtube_client = build('youtube', 'v3', developerKey=api_key)
            else:
                print("Warning: YOUTUBE_API_KEY not found")
        except ImportError:
            print("Warning: googleapiclient not available")
    return _youtube_client

# Socratic persona for the chatbot
SYSTEM_PROMPT = """
You are a Socratic Coach who helps learners reach aha-moments through guided discovery. You adapt to the last user message, move one step at a time, and avoid repeating openings.

**GUARDRAILS:**
- Always acknowledge the user's latest message in 1 short line (reflect it or rephrase simply).
- If the user says "I don't know", is clearly confused, or uses an unfamiliar/incorrect term, give a micro-lesson: 1–2 plain sentences to anchor the concept, then ask exactly one targeted question.
- Clarify typos or ambiguous terms politely and briefly. If confident (e.g., "toque" → "torque"), note the correction in passing and continue.
- Never reuse broad openers like "Before we begin…" or "Perfect! Before we dive in…" after the first turn.
- One question per turn, placed at the end. No stacked questions.
- Prefer concrete examples, analogies, or tiny thought experiments.
- Frequently check understanding by asking the learner to restate in their own words (but not every turn).
- Keep language plain; define any unavoidable jargon immediately.

**RESPONSE STRUCTURE (DEFAULT):**
- Recap: 1 short line that mirrors or affirms the user's last message.
- Micro-step: 1–3 short lines (definition, analogy, or example) tailored to their message.
- Your turn: end with exactly one targeted question.

**EXAMPLE BEHAVIOR:**
If user says "I don't know torque" → Recap: "You're not sure what torque is." Micro-step: "Torque is twist-force: how strongly a push makes something rotate. Pushing farther from the hinge makes a door turn more easily." Your turn: "If you push near the door's hinges vs the handle, which needs less force to rotate the door?"

If user has typo like "toque" → "I'm assuming you meant 'torque' (the twist-force). If you meant something else, tell me."

**YOUR MISSION:**
Surface and resolve confusion, rebuild shaky knowledge, and help users "own" the material through questioning, analogies, and memorable, back-and-forth exploration. Make every idea memorable with vivid analogies or everyday situations.

**RESPONSE STYLE:**
Keep responses conversational, warm, and encouraging. Use everyday language and concrete examples. Turn "I don't know" into progress. Make learning enjoyable and human, not mechanical. Always encourage reflection, summarization, and application.
"""

@app.route('/')
def serve_app():
    """Serve the main application"""
    return send_from_directory('.', 'index_professional.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    stats = db.get_user_stats()
    return jsonify({
        "status": "running", 
        "message": "Scoratis API is healthy",
        "version": "2.0",
        "stats": stats
    })

# ==================== JOURNAL ENDPOINTS ====================

@app.route('/journals', methods=['GET'])
def get_journals():
    """Get all journals with optional filtering"""
    folder_id = request.args.get('folder_id', type=int)
    search_query = request.args.get('search')
    
    try:
        journals = db.get_journals(folder_id=folder_id, search_query=search_query)
        return jsonify(journals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/journals', methods=['POST'])
def create_journal():
    """Create a new journal entry"""
    data = request.json
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    tags = data.get('tags', [])
    folder_id = data.get('folder_id')
    
    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400
    
    try:
        journal_id = db.create_journal(title, content, tags, folder_id)
        return jsonify({"id": journal_id, "message": "Journal created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/journals/<int:journal_id>', methods=['PUT'])
def update_journal(journal_id):
    """Update a journal entry"""
    data = request.json
    
    try:
        success = db.update_journal(
            journal_id,
            title=data.get('title'),
            content=data.get('content'),
            tags=data.get('tags'),
            folder_id=data.get('folder_id')
        )
        
        if success:
            return jsonify({"message": "Journal updated successfully"})
        else:
            return jsonify({"error": "No changes made"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/journals/<int:journal_id>', methods=['DELETE'])
def delete_journal(journal_id):
    """Delete a journal entry"""
    try:
        db.delete_journal(journal_id)
        return jsonify({"message": "Journal deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/journals/<int:journal_id>/share', methods=['POST'])
def toggle_journal_sharing(journal_id):
    """Toggle journal sharing status"""
    try:
        share_token = db.share_journal(journal_id)
        share_url = f"{request.host_url}shared/{share_token}"
        return jsonify({
            "message": "Journal sharing toggled successfully",
            "share_token": share_token,
            "share_url": share_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== FOLDER ENDPOINTS ====================

@app.route('/folders', methods=['GET'])
def get_folders():
    """Get all folders"""
    try:
        folders = db.get_folders()
        return jsonify(folders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/folders', methods=['POST'])
def create_folder():
    """Create a new folder"""
    data = request.json
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    color = data.get('color', '#8A2BE2')
    
    if not name:
        return jsonify({"error": "Folder name is required"}), 400
    
    try:
        folder_id = db.create_folder(name, description, color)
        return jsonify({"id": folder_id, "message": "Folder created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/folders/<int:folder_id>', methods=['PUT'])
def update_folder(folder_id):
    """Update a folder"""
    data = request.json
    
    try:
        success = db.update_folder(
            folder_id,
            name=data.get('name'),
            description=data.get('description'),
            color=data.get('color')
        )
        
        if success:
            return jsonify({"message": "Folder updated successfully"})
        else:
            return jsonify({"error": "No changes made"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/folders/<int:folder_id>', methods=['DELETE'])
def delete_folder(folder_id):
    """Delete a folder"""
    try:
        db.delete_folder(folder_id)
        return jsonify({"message": "Folder deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== CHAT ENDPOINT ====================

# Simple conversation memory storage (in production, use Redis or database)
conversation_memory = {}

@app.route('/chat', methods=['POST'])
def chat():
    """Chat with Scoratis AI assistant with conversation memory"""
    data = request.json
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')  # Allow frontend to provide session ID
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    genai = get_genai()
    
    def generate_fallback(user_message):
        """Generate contextual fallback response based on user message"""
        msg_lower = user_message.lower().strip()
        
        # Handle overwhelm/everything responses
        if any(word in msg_lower for word in ["everything", "nothing", "all of it", "all", "i am not understanding anything", "not understanding"]):
            return "Feeling overwhelmed? Let's start with something tiny and concrete. Picture a door opening - that's rotation! What makes a door easy or hard to push open?"
        
        # Handle substantial physics answers (acknowledge good thinking!)
        if len(msg_lower) > 30 and any(word in msg_lower for word in ["force", "gravity", "spin", "rotation", "centrifugal", "weight"]):
            return f"Excellent thinking! You mentioned forces - that's exactly the right track. Now here's a key question: if you spin a coin on a table, what do you think slows it down and makes it stop?"
        
        # Handle "don't know" or confusion with better context
        if any(phrase in msg_lower for phrase in ["don't know", "dont know", "idk", "confused", "no idea"]):
            if "torque" in msg_lower or "toque" in msg_lower:
                return "You're unsure what torque means. Quick anchor: torque is the 'twist' effect of a force—pushing farther from the pivot makes rotation easier. If you push a door near the hinges vs the handle, where does the same push create more rotation?"
            elif any(word in msg_lower for word in ["rotation", "spin", "turn"]):
                return "You're feeling lost about rotation. Here's a simple start: rotation is just spinning around a center point, like a wheel or door. What happens when you try to stop a spinning coin with your finger?"
            else:
                return "That's completely normal when learning something new! Let's try a concrete example: imagine pushing a door. Would it be easier to push near the hinges or near the handle?"
        
        # Handle typos and corrections
        if "toque" in msg_lower and "torque" not in msg_lower:
            return "I'm assuming you meant 'torque' (the twist-force that causes rotation). Torque is like the 'oomph' that makes things spin. Are you asking how torque differs from regular force?"
        
        # Handle basic single words or very short responses
        if len(msg_lower) < 15 or msg_lower in ["rotation", "physics", "hard", "difficult", "clear", "small", "tiny"]:
            return f"You said '{user_message}'. Let's connect this to something you can picture. Think of a spinning coin - what do you think makes it start spinning, and what makes it wobble and fall over?"
        
        # Handle learning requests 
        if any(phrase in msg_lower for phrase in ["teach me", "learn", "start", "beginning", "begenning"]):
            return "Perfect! You want to learn from the beginning. Let's start with the most basic question: when you open a door, do you push near the hinges or near the handle? Why do you think that is?"
        
        # Handle specific physics concepts
        if "space" in msg_lower and ("torque" in msg_lower or "rotation" in msg_lower):
            return "You're asking about torque vs space concepts. Torque is about causing rotation; space is where things exist and move. Are you wondering how rotational motion works in different environments?"
        
        # Default fallback - more engaging
        return f"I hear you saying '{user_message}'. Let's make this super concrete: imagine you're trying to loosen a tight jar lid. Where do you grip it, and how do you twist? What makes it easier or harder?"
    
    if not genai:
        response = generate_fallback(user_message)
        return jsonify({"reply": response, "source": "fallback"})
    
    try:
        # Set socket timeout for faster response
        socket.setdefaulttimeout(15)
        
        # Get or initialize conversation history
        if session_id not in conversation_memory:
            conversation_memory[session_id] = []
        
        # Save user message to database
        db.add_chat_message(session_id, 'user', user_message)
        
        # Add user message to in-memory history for this request
        conversation_memory[session_id].append(f"Human: {user_message}")
        
        # Keep only last 10 messages to avoid token limits
        if len(conversation_memory[session_id]) > 10:
            conversation_memory[session_id] = conversation_memory[session_id][-10:]
        
        # Build conversation context
        conversation_context = "\n".join(conversation_memory[session_id])
        full_prompt = f"""Previous conversation:
{conversation_context}

Please continue the conversation naturally, maintaining the Socratic teaching approach while building on what has been discussed.

Important: Don't use generic openers ('Before we begin…', 'Perfect! Before…', 'Excellent! Before…'). Acknowledge the last user message, give a micro-anchor if needed, and ask one targeted question."""
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        generation_config = genai.GenerationConfig(
            max_output_tokens=300,  # Allow for more detailed anchor-question responses
            temperature=0.7,  # Slightly more focused for teaching
            top_p=0.9
        )
        
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        # Save AI response to database
        db.add_chat_message(session_id, 'ai', response.text)
        
        # Add AI response to history
        conversation_memory[session_id].append(f"Scoratis: {response.text}")
        
        return jsonify({"reply": response.text, "source": "ai", "session_id": session_id})
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        response = generate_fallback(user_message)
        # Save fallback response to database
        db.add_chat_message(session_id, 'ai', response)
        return jsonify({"reply": response, "source": "fallback"})

@app.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Clear conversation memory for a session (but keep in database)"""
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    
    # Clear from memory only - DO NOT delete from database
    if session_id in conversation_memory:
        del conversation_memory[session_id]
    
    # Note: We're NOT calling db.clear_conversation() here anymore
    # Conversations should persist in database for history
    
    return jsonify({"message": "Conversation memory cleared", "session_id": session_id})

@app.route('/chat/history', methods=['GET'])
def get_conversation_history():
    """Get list of recent conversations"""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 conversations
        conversations = db.get_conversation_history(user_id=1, limit=limit)
        return jsonify({"conversations": conversations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/conversation/<session_id>', methods=['GET'])
def get_conversation_messages(session_id):
    """Get all messages for a specific conversation"""
    try:
        messages = db.get_conversation_messages(session_id, user_id=1)
        return jsonify({"messages": messages, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/conversation/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Move conversation to trash or permanently delete it"""
    try:
        data = request.json or {}
        permanent = data.get('permanent', False)
        
        db.delete_conversation(conversation_id, user_id=1, permanent=permanent)
        
        if permanent:
            return jsonify({"message": "Conversation permanently deleted"})
        else:
            return jsonify({"message": "Conversation moved to trash"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/trash', methods=['GET'])
def get_trash():
    """Get conversations in trash"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        conversations = db.get_conversation_history(user_id=1, limit=limit, include_deleted=True)
        return jsonify({"conversations": conversations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/conversation/<int:conversation_id>/restore', methods=['POST'])
def restore_conversation(conversation_id):
    """Restore conversation from trash"""
    try:
        db.restore_conversation(conversation_id, user_id=1)
        return jsonify({"message": "Conversation restored successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/trash/empty', methods=['POST'])
def empty_trash():
    """Permanently delete all conversations in trash"""
    try:
        db.empty_trash(user_id=1)
        return jsonify({"message": "Trash emptied successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== VIDEO ENDPOINTS ====================

@app.route('/videos/search', methods=['GET'])
def search_videos():
    """Search for videos using YouTube API"""
    query = request.args.get('q', '').strip()
    max_results = min(int(request.args.get('max_results', 12)), 25)  # Limit to 25 max
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    youtube_client = get_youtube_client()
    
    # Fallback sample videos if YouTube API is not available
    if not youtube_client:
        sample_videos = [
            {
                "video_id": "dQw4w9WgXcQ",
                "title": f"Educational Content: {query} - Introduction",
                "channel": "Educational Channel",
                "thumbnail": "https://via.placeholder.com/320x180/8A2BE2/FFFFFF?text=Video+1",
                "description": f"Learn about {query} in this comprehensive introduction.",
                "published_at": "2024-01-01T00:00:00Z",
                "duration": "10:30",
                "view_count": "1.2M"
            },
            {
                "video_id": "dQw4w9WgXcQ",
                "title": f"Advanced {query} Techniques",
                "channel": "Science Academy",
                "thumbnail": "https://via.placeholder.com/320x180/00BFFF/FFFFFF?text=Video+2",
                "description": f"Dive deeper into {query} with advanced concepts.",
                "published_at": "2024-01-02T00:00:00Z",
                "duration": "15:45",
                "view_count": "850K"
            }
        ]
        return jsonify({"videos": sample_videos[:max_results], "source": "sample"})
    
    try:
        # Set timeout for faster response
        socket.setdefaulttimeout(10)
        
        # Search for videos
        search_response = youtube_client.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=max_results,
            order='relevance',
            safeSearch='moderate',
            videoEmbeddable='true'
        ).execute()
        
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        
        if not video_ids:
            return jsonify({"videos": [], "message": "No videos found"})
        
        # Get additional video details
        videos_response = youtube_client.videos().list(
            part='statistics,contentDetails',
            id=','.join(video_ids)
        ).execute()
        
        # Create video details map
        video_details = {item['id']: item for item in videos_response.get('items', [])}
        
        formatted_videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']
            details = video_details.get(video_id, {})
            
            # Parse duration
            duration = details.get('contentDetails', {}).get('duration', 'PT0S')
            duration_formatted = parse_youtube_duration(duration)
            
            # Get view count
            view_count = details.get('statistics', {}).get('viewCount', '0')
            view_count_formatted = format_view_count(int(view_count))
            
            video_data = {
                "video_id": video_id,
                "title": snippet['title'],
                "channel": snippet['channelTitle'],
                "thumbnail": snippet['thumbnails'].get('medium', {}).get('url', ''),
                "description": snippet.get('description', '')[:200] + '...' if len(snippet.get('description', '')) > 200 else snippet.get('description', ''),
                "published_at": snippet['publishedAt'],
                "duration": duration_formatted,
                "view_count": view_count_formatted
            }
            formatted_videos.append(video_data)
            
            # Add to video history
            try:
                db.add_video_to_history(
                    video_id, 
                    snippet['title'], 
                    snippet['channelTitle'],
                    video_data['thumbnail'],
                    query
                )
            except:
                pass  # Ignore history errors
        
        return jsonify({"videos": formatted_videos, "source": "youtube"})
        
    except Exception as e:
        print(f"Error fetching videos: {e}")
        error_msg = str(e).lower()
        
        if "quotaexceeded" in error_msg:
            return jsonify({"error": "YouTube API quota exceeded. Please try again later."}), 429
        elif "keyinvalid" in error_msg or "forbidden" in error_msg:
            return jsonify({"error": "Invalid YouTube API key."}), 401
        else:
            return jsonify({"error": f"Failed to fetch videos: {str(e)}"}), 500

@app.route('/videos/history', methods=['GET'])
def get_video_history():
    """Get video watch history"""
    limit = min(int(request.args.get('limit', 50)), 100)
    
    try:
        history = db.get_video_history(limit=limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== UTILITY FUNCTIONS ====================

def parse_youtube_duration(duration):
    """Parse YouTube duration format (PT1H2M3S) to readable format"""
    import re
    
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    
    if not match:
        return "0:00"
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def format_view_count(count):
    """Format view count to readable format"""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    else:
        return str(count)

# ==================== STATISTICS ENDPOINT ====================

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get user statistics"""
    try:
        stats = db.get_user_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 Starting Scoratis Professional Server...")
    print("📊 Database initialized successfully")
    print("🔑 API keys loaded from environment")
    print("🌐 Server starting on http://127.0.0.1:5001")
    app.run(debug=True, port=5001, host='127.0.0.1')