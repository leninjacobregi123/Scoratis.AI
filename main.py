from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
# Use official YouTube Data API client
from googleapiclient.discovery import build
import json

load_dotenv()

app = Flask(__name__)
CORS(app) 

# Configure the Gemini API key (lazy loading)
api_key = os.getenv("GEMINI_API_KEY")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

def get_gemini_client():
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Gemini API Configuration Error: {e}")
        return None

def get_youtube_client():
    if not youtube_api_key:
        return None
    try:
        return build('youtube', 'v3', developerKey=youtube_api_key)
    except Exception as e:
        print(f"YouTube API Configuration Error: {e}")
        return None

# Socratic persona for the chatbot
system_prompt = """
You are Scoratis, an AI assistant inspired by the philosopher Socrates. 
Your purpose is to help users with journaling and self-discovery through thoughtful questioning and dialogue. 
- Respond in a calm, inquisitive, and encouraging tone.
- Instead of giving direct answers, guide users to find their own answers by asking probing questions.
- Use the Socratic method: break down complex problems into smaller questions.
- Keep your responses concise and focused on helping the user reflect.
- Acknowledge the user's input before gently guiding them deeper.
"""

@app.route('/')
def health_check():
    return jsonify({"status": "running", "message": "Scoratis API is healthy"})

@app.route('/chat', methods=['POST'])
def chat():
    if not get_gemini_client():
        return jsonify({"error": "Gemini API key is not configured on the server."}), 500

    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt
        )
        # Add timeout and faster generation config
        generation_config = genai.GenerationConfig(
            max_output_tokens=200,  # Limit response length for speed
            temperature=0.7,
        )
        response = model.generate_content(
            user_message,
            generation_config=generation_config,
            request_options={"timeout": 10}  # 10 second timeout
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Return a fallback response instead of error
        fallback_response = f"I appreciate your question about journaling. What specific aspect of your thoughts would you like to explore further?"
        return jsonify({"reply": fallback_response})

@app.route('/get_videos', methods=['GET'])
def get_videos():
    youtube_client = get_youtube_client()
    if not youtube_client:
        return jsonify({"error": "YouTube API is not configured. Please add a YOUTUBE_API_KEY to your .env file."}), 500
        
    try:
        query = request.args.get('q', 'educational science')
        if not query:
            return jsonify({"error": "Search query cannot be empty"}), 400

        # Use YouTube Data API with timeout and error handling
        import socket
        socket.setdefaulttimeout(10)  # 10 second timeout for all socket operations
        
        search_response = youtube_client.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=4,  # Further reduced for speed
            relevanceLanguage='en',
            order='relevance'
        ).execute()

        formatted_videos = []
        for search_result in search_response.get('items', []):
            formatted_videos.append({
                'title': search_result['snippet']['title'],
                'thumbnail': search_result['snippet']['thumbnails']['medium']['url'],
                'channel': search_result['snippet']['channelTitle'],
                'url_suffix': f"/watch?v={search_result['id']['videoId']}"
            })
            
        return jsonify(formatted_videos)
    except Exception as e:
        print(f"Error fetching videos: {e}")
        # Return a more specific error message
        error_msg = str(e).lower()
        if "quotaexceeded" in error_msg:
            return jsonify({"error": "YouTube API quota exceeded. Please try again later."}), 500
        elif "keyinvalid" in error_msg or "forbidden" in error_msg:
            return jsonify({"error": "Invalid YouTube API key. Please check your YOUTUBE_API_KEY in the .env file."}), 500
        elif "failed to establish a new connection" in error_msg:
            return jsonify({"error": "Network connection error. Please check your internet connection."}), 500
        return jsonify({"error": f"Failed to fetch videos from YouTube: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

