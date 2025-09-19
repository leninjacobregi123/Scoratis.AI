from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return jsonify({"status": "running", "message": "Test server is healthy"})

@app.route('/test_chat', methods=['POST'])
def test_chat():
    data = request.json
    message = data.get('message', 'No message')
    return jsonify({"reply": f"Echo: {message}"})

@app.route('/test_videos')
def test_videos():
    # Return mock video data for testing
    mock_videos = [
        {
            "title": "Sample Science Video 1",
            "thumbnail": "https://via.placeholder.com/320x180",
            "channel": "Science Channel",
            "url_suffix": "/watch?v=dQw4w9WgXcQ"
        },
        {
            "title": "Sample Science Video 2", 
            "thumbnail": "https://via.placeholder.com/320x180",
            "channel": "Educational Channel",
            "url_suffix": "/watch?v=dQw4w9WgXcQ"
        }
    ]
    return jsonify(mock_videos)

if __name__ == '__main__':
    app.run(debug=True, port=5002, host='127.0.0.1')