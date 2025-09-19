from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app) 

@app.route('/')
def health_check():
    return jsonify({"status": "running", "message": "Scoratis API is healthy"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Simple Socratic responses for now (to avoid slow AI API)
    socratic_responses = [
        "What aspects of this topic resonate most deeply with you?",
        "Can you tell me more about what prompted this reflection?",
        "What patterns do you notice in your thinking about this?",
        "How might exploring this further benefit your understanding?",
        "What questions arise for you when you consider this more deeply?",
        "What would it mean for you to understand this better?"
    ]
    
    import random
    response = random.choice(socratic_responses)
    return jsonify({"reply": response})

@app.route('/get_videos', methods=['GET'])
def get_videos():
    # Return sample educational videos for now (to avoid slow YouTube API)
    query = request.args.get('q', 'science')
    
    sample_videos = [
        {
            "title": f"Educational Video about {query} - Part 1",
            "thumbnail": "https://via.placeholder.com/320x180/8A2BE2/FFFFFF?text=Video+1",
            "channel": "Educational Channel",
            "url_suffix": "/watch?v=dQw4w9WgXcQ"
        },
        {
            "title": f"Learning {query} - Fundamentals",
            "thumbnail": "https://via.placeholder.com/320x180/00BFFF/FFFFFF?text=Video+2",
            "channel": "Science Academy",
            "url_suffix": "/watch?v=dQw4w9WgXcQ"
        },
        {
            "title": f"Advanced {query} Concepts",
            "thumbnail": "https://via.placeholder.com/320x180/8A2BE2/FFFFFF?text=Video+3",
            "channel": "Knowledge Hub",
            "url_suffix": "/watch?v=dQw4w9WgXcQ"
        },
        {
            "title": f"{query} Explained Simply",
            "thumbnail": "https://via.placeholder.com/320x180/00BFFF/FFFFFF?text=Video+4",
            "channel": "Simple Learning",
            "url_suffix": "/watch?v=dQw4w9WgXcQ"
        }
    ]
    
    return jsonify(sample_videos)

if __name__ == '__main__':
    print("Starting Scoratis server...")
    app.run(debug=True, port=5000, host='127.0.0.1')