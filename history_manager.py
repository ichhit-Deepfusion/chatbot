import os
import json
from datetime import datetime

HISTORY_DIR = "chat_history"

def ensure_history_dir():
    """Ensure the chat history directory exists."""
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def get_all_chats():
    """Retrieve all saved chats, sorted by last modified timestamp (newest first)."""
    ensure_history_dir()
    chats = []
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chats.append({
                        "id": data.get("session_id", filename.replace(".json", "")),
                        "title": data.get("title", "Untitled Chat"),
                        "timestamp": data.get("timestamp", 0)
                    })
            except Exception:
                # Silently ignore malformed files
                pass
    # Sort by timestamp descending
    chats.sort(key=lambda x: x["timestamp"], reverse=True)
    return chats

def load_chat(chat_id):
    """Load a specific chat session's data."""
    ensure_history_dir()
    filepath = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_chat(chat_id, title, messages, file_context="", last_uploaded_filename=None, token_tracker_data=None):
    """Save or update a chat session's data."""
    ensure_history_dir()
    filepath = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    
    if token_tracker_data is None:
        token_tracker_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
    data = {
        "session_id": chat_id,
        "title": title,
        "messages": messages,
        "file_context": file_context,
        "last_uploaded_filename": last_uploaded_filename,
        "token_tracker_data": token_tracker_data,
        "timestamp": datetime.now().timestamp()
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_chat(chat_id):
    """Delete a chat session's file."""
    ensure_history_dir()
    filepath = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception:
            return False
    return False
