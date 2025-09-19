# Scoratis - Professional Journaling & Learning Platform

Scoratis is a powerful journaling and learning platform that combines AI-powered Socratic questioning with organized knowledge management. Built with Flask and modern web technologies, it provides a seamless experience for reflection, learning, and knowledge organization.

## 🌟 Features

### Journaling System
- **Rich Text Journaling**: Create and manage detailed journal entries
- **Tagging System**: Organize entries with custom tags for easy retrieval
- **Folder Organization**: Categorize journals into folders with custom colors
- **Sharing Capabilities**: Share journals with unique shareable links

### AI-Powered Learning
- **Socratic AI Assistant**: Engage with an AI tutor that uses Socratic questioning to deepen understanding
- **Conversation History**: Maintain and organize chat conversations with the AI
- **Trash Management**: Move conversations to trash and restore or permanently delete them

### Video Learning Integration
- **YouTube Search**: Search for educational videos directly within the platform
- **Video History**: Track watched videos for continued learning
- **Video Recommendations**: Find relevant content based on your interests

### User Management
- **Statistics Dashboard**: Track your journaling and learning progress
- **User Preferences**: Customize themes and settings
- **Organized Interface**: Clean, modern UI with dark theme

## 🏗️ Architecture

### Backend (Flask API)
- RESTful API built with Flask
- SQLite database for data persistence
- CORS support for frontend integration
- Modular design with separate endpoints for journals, folders, chat, and videos

### Frontend (HTML/CSS/JavaScript)
- Single-page application with responsive design
- Tailwind CSS for modern styling
- Lucide Icons for beautiful UI elements
- Real-time chat interface with typing indicators

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scoratis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_google_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### Running the Application

Use the provided startup scripts for easy management:

#### Smart Startup (Recommended)
```bash
./start_servers.sh
```
This script automatically:
- Kills any processes on ports 5001 and 8080
- Starts both backend and frontend servers
- Performs health checks
- Monitors server health
- Provides graceful shutdown with Ctrl+C

#### Development Mode with Auto-Restart
```bash
./auto_restart.sh
```
This script:
- Monitors files for changes
- Automatically restarts servers on code changes
- Perfect for active development

#### Manual Port Management
```bash
./kill_ports.sh          # Kills processes on default ports 5001, 8080
./kill_ports.sh 3000     # Kill specific port
./kill_ports.sh 5001 8080 3000  # Kill multiple ports
```

### Access the Application
- **Frontend Application**: http://127.0.0.1:8080/index_professional.html
- **Backend API**: http://127.0.0.1:5001/
- **API Health Check**: http://127.0.0.1:5001/stats

## 📁 Project Structure
```
scoratis/
├── main_professional.py     # Flask backend server
├── database.py             # SQLite database management
├── index_professional.html # Main frontend application
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (not included in repo)
├── README.md              # This file
├── README_SCRIPTS.md      # Detailed scripts documentation
├── start_servers.sh       # Smart startup script
├── auto_restart.sh        # Development auto-restart script
├── kill_ports.sh          # Port management script
├── logs/                  # Server log directory
├── scoratis.db            # SQLite database file
└── scripts/               # Utility scripts
```

## 🛠️ API Endpoints

### Journal Management
- `GET /journals` - Get all journals
- `POST /journals` - Create a new journal
- `PUT /journals/<id>` - Update a journal
- `DELETE /journals/<id>` - Delete a journal
- `POST /journals/<id>/share` - Toggle journal sharing

### Folder Management
- `GET /folders` - Get all folders
- `POST /folders` - Create a new folder
- `PUT /folders/<id>` - Update a folder
- `DELETE /folders/<id>` - Delete a folder

### AI Chat
- `POST /chat` - Send a message to the AI
- `POST /chat/clear` - Clear conversation memory
- `GET /chat/history` - Get conversation history
- `GET /chat/conversation/<session_id>` - Get messages for a conversation
- `DELETE /chat/conversation/<id>` - Delete/move conversation to trash
- `GET /chat/trash` - Get trashed conversations
- `POST /chat/conversation/<id>/restore` - Restore conversation from trash
- `POST /chat/trash/empty` - Empty trash permanently

### Video Search
- `GET /videos/search` - Search for YouTube videos
- `GET /videos/history` - Get video watch history

### Statistics
- `GET /stats` - Get user statistics
- `GET /health` - Health check endpoint

## 🎯 Development Scripts

### start_servers.sh
Smart startup script that manages ports and starts both servers with error handling.

### auto_restart.sh
Development mode script that watches files for changes and automatically restarts servers.

### kill_ports.sh
Utility script to kill processes on specific ports.

## 📊 Database Schema

The application uses SQLite with the following tables:
- `users` - User information
- `folders` - Journal organization folders
- `journals` - Journal entries with tagging support
- `video_history` - Watched video tracking
- `user_preferences` - User settings and preferences
- `conversations` - Chat conversation tracking
- `chat_messages` - Individual chat messages

## 🔐 Environment Variables

Create a `.env` file with the following variables:
```
GEMINI_API_KEY=your_google_gemini_api_key
YOUTUBE_API_KEY=your_youtube_data_api_key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- YouTube Data API for video search functionality
- Tailwind CSS for styling framework
- Lucide Icons for beautiful icons